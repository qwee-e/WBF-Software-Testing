"""Generation, transformations, paired-output checks and reproducible evidence."""
import copy
import hashlib
import json
import os
import random
from collections import Counter
from pathlib import Path

import numpy as np
from hypothesis import example, strategies as st

from ensemble_boxes.ensemble_boxes_wbf import weighted_boxes_fusion

MODES = ('avg', 'max', 'box_and_model_avg', 'absent_model_aware_avg')
ATOL, RTOL = 1e-6, 1e-5


def coverage_examples(test):
    """Eight explicit anchors guarantee mode/flag coverage beyond random sampling."""
    for mode in MODES:
        for overflow in (False, True):
            data = dict(boxes_list=[[[.14, .14, .23, .23], [.4, .4, .49, .49]],
                                    [[.141, .14, .231, .23], [.401, .4, .491, .49]]],
                        scores_list=[[.8, .6], [.35, .25]], labels_list=[[0, 1], [0, 1]],
                        weights=[1., 2.], iou_thr=.45, skip_box_thr=.05,
                        conf_type=mode, allows_overflow=overflow)
            test = example(data=data)(test)
    return test


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def rng_for(value, salt):
    return random.Random(int(digest([salt, value])[:16], 16))


@st.composite
def stable_inputs(draw):
    """Separated clusters; unique effective scores; no unstable IoU decisions.

    All endpoints within .002 of .09-wide template boxes. Even a dynamic
    convex centroid overlaps a member with IoU > .69; threshold <= .60.
    Different templates are disjoint. Labels separate overlapping classes.
    """
    m = draw(st.integers(2, 6))
    classes = draw(st.integers(1, 3))
    clusters = draw(st.integers(1, 3))
    weights = draw(st.lists(st.sampled_from([.5, 1., 2., 4.]), min_size=m, max_size=m))
    records = [(model, label, cluster) for label in range(classes)
               for cluster in range(clusters) for model in range(2)]
    records += draw(st.lists(st.tuples(st.integers(0, m - 1),
                                    st.integers(0, classes - 1),
                                    st.integers(0, clusters - 1)), max_size=10))
    result = dict(boxes_list=[[] for _ in range(m)], scores_list=[[] for _ in range(m)],
                  labels_list=[[] for _ in range(m)], weights=weights,
                  iou_thr=draw(st.sampled_from([.3, .45, .6])),
                  skip_box_thr=draw(st.sampled_from([0., .02, .05, .1])),
                  conf_type=draw(st.sampled_from(MODES)), allows_overflow=draw(st.booleans()))
    jitter = draw(st.lists(st.integers(-2, 2), min_size=4 * len(records), max_size=4 * len(records)))
    for i, (model, label, cluster) in enumerate(records):
        start = .14 + .26 * cluster
        box = [start, start, start + .09, start + .09]
        box = [v + .001 * jitter[4 * i + j] for j, v in enumerate(box)]
        effective_score = .05 + .4 * (i + 1) / (len(records) + 1)
        result['boxes_list'][model].append(box)
        result['scores_list'][model].append(effective_score / weights[model])
        result['labels_list'][model].append(label)
    return result


def model_permutation(data, order):
    other = copy.deepcopy(data)
    for key in ('boxes_list', 'scores_list', 'labels_list', 'weights'):
        other[key] = [copy.deepcopy(data[key][i]) for i in order]
    return other


def box_permutation(data, orders):
    other = copy.deepcopy(data)
    for key in ('boxes_list', 'scores_list', 'labels_list'):
        other[key] = [[copy.deepcopy(data[key][m][i]) for i in order]
                      for m, order in enumerate(orders)]
    return other


def map_boxes(data, transform):
    other = copy.deepcopy(data)
    other['boxes_list'] = [[list(transform(box)) for box in boxes] for boxes in data['boxes_list']]
    return other


def map_output(output, transform):
    return (np.array([transform(b) for b in output[0]], dtype=float).reshape(-1, 4),
            output[1].copy(), output[2].copy())


def check_output(output):
    boxes, scores, labels = output
    assert boxes.shape == (len(scores), 4), 'box/score shape mismatch'
    assert scores.shape == labels.shape == (len(boxes),), 'score/label shape mismatch'
    assert all(np.isfinite(a).all() for a in output), 'nonfinite output'
    assert (boxes >= -ATOL).all() and (boxes <= 1 + ATOL).all(), 'coordinate outside [0,1]'
    assert (boxes[:, 2:] > boxes[:, :2]).all(), 'nonpositive area'
    assert (scores >= -ATOL).all(), 'negative score'


def same_output(expected, actual):
    """Bijective tuple matching; neither row order nor independent sorts are an oracle."""
    check_output(expected)
    check_output(actual)
    if len(expected[0]) != len(actual[0]):
        return False
    candidates = [[j for j in range(len(actual[0]))
                   if expected[2][i] == actual[2][j]
                   and np.allclose(expected[0][i], actual[0][j], atol=ATOL, rtol=RTOL)
                   and np.isclose(expected[1][i], actual[1][j], atol=ATOL, rtol=RTOL)]
                  for i in range(len(expected[0]))]
    matched = {}

    def augment(i, seen):
        for j in candidates[i]:
            if j not in seen:
                seen.add(j)
                if j not in matched or augment(matched[j], seen):
                    matched[j] = i
                    return True
        return False

    return all(augment(i, set()) for i in range(len(candidates)))


def json_safe(value):
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


class Audit:
    def __init__(self, case):
        self.case = case
        self.counts = Counter()
        self.configurations = Counter()
        self.samples = []
        self.findings = []

    def source(self, data):
        self.counts['source_examples'] += 1
        self.configurations[f"{data['conf_type']}/overflow={data['allows_overflow']}"] += 1

    def call(self, data):
        self.counts['wbf_calls'] += 1
        return weighted_boxes_fusion(**copy.deepcopy(data))

    def compare(self, source, transformed, expected, actual, transformation):
        self.counts['metamorphic_comparisons'] += 1
        passed = same_output(expected, actual)
        evidence = dict(input=source, transformed_input=transformed, expected=expected,
                        actual=actual, transformation=transformation, passed=passed)
        if len(self.samples) < 3:
            self.samples.append(evidence)
        if not passed:
            self.findings.append(evidence)
        assert passed, f'{self.case}: paired outputs differ; evidence saved by fixture'

    def save(self):
        directory = Path(os.environ.get('AI_RESULTS_DIR', 'ai_test_results')) / self.case
        directory.mkdir(parents=True, exist_ok=True)
        payload = dict(case=self.case, counts=dict(self.counts), configurations=dict(self.configurations),
                       tolerance=dict(atol=ATOL, rtol=RTOL), samples=self.samples, findings=self.findings)
        (directory / 'evidence.json').write_text(json.dumps(json_safe(payload), ensure_ascii=False,
                                                indent=2, allow_nan=False), encoding='utf-8')
