import copy
import random

import numpy as np

from ai_tests.support import MODES, check_output


def small_score_case(rng, magnitude, mode):
    boxes = [[[.1, .1, .2, .2], [.4, .4, .5, .5]],
             [[.101, .1, .201, .2], [.401, .4, .501, .5]],
             [[.099, .1, .199, .2], [.399, .4, .499, .5]]]
    scores = [[magnitude * rng.uniform(.1, 1) for _ in model] for model in boxes]
    return dict(boxes_list=boxes, scores_list=scores, labels_list=[[0, 1]] * 3,
                weights=[.5, 1., 4.], iou_thr=.5, skip_box_thr=0.,
                conf_type=mode, allows_overflow=False)


def normalize_scores(data):
    transformed = copy.deepcopy(data)
    maximum = max(score for model in data['scores_list'] for score in model)
    transformed['scores_list'] = [[score / maximum for score in model]
                                  for model in data['scores_list']]
    return transformed, maximum


def ordered(output):
    boxes, scores, labels = output
    order = np.argsort(labels, kind='stable')
    return boxes[order], scores[order], labels[order]


def test_small_positive_score_stability(audit):
    rng = random.Random(20260918012)
    magnitudes = [1e-2, 1e-4, 1e-8]
    for index in range(400):
        mode = MODES[index % 4]
        data = small_score_case(rng, magnitudes[index % 3], mode)
        audit.source(data)
        baseline = ordered(audit.call(data))
        transformed, maximum = normalize_scores(data)
        normalized = ordered(audit.call(transformed))
        check_output(baseline)
        check_output(normalized)
        assert np.array_equal(baseline[2], normalized[2])
        assert np.allclose(baseline[0], normalized[0], rtol=1e-5, atol=1e-6)
        assert np.allclose(baseline[1] / maximum, normalized[1], rtol=2e-5, atol=0)
        audit.counts['main_normalization_comparisons'] += 1

    exploratory = [1e-16, 1e-30, 1e-40]
    for index in range(100):
        mode = MODES[index % 4]
        data = small_score_case(rng, exploratory[index % 3], mode)
        audit.counts['exploratory_examples'] += 1
        original = audit.call(data)
        transformed, maximum = normalize_scores(data)
        normalized = audit.call(transformed)
        finite = all(np.isfinite(part).all() for part in original)
        positive = bool(len(original[1]) and np.all(original[1] > 0))
        relation = False
        if finite and positive and len(original[0]) == len(normalized[0]):
            left, right = ordered(original), ordered(normalized)
            relation = (np.array_equal(left[2], right[2])
                        and np.allclose(left[0], right[0], rtol=1e-5, atol=1e-6)
                        and np.allclose(left[1] / maximum, right[1], rtol=2e-5, atol=0))
        if not finite:
            audit.counts['exploratory_nonfinite'] += 1
        if not positive:
            audit.counts['exploratory_zero_or_empty_scores'] += 1
        if not relation:
            audit.counts['exploratory_relation_differences'] += 1
            if len(audit.findings) < 10:
                audit.findings.append(dict(kind='exploratory_small_score_difference',
                                           magnitude=exploratory[index % 3], mode=mode,
                                           input=data, original=original,
                                           normalized=normalized, scale=maximum))
