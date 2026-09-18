import copy
import random

import numpy as np

from ai_tests.support import ATOL, MODES, RTOL, check_output


def make_case(rng):
    model_count = rng.randint(2, 8)
    data = dict(boxes_list=[[] for _ in range(model_count)],
                scores_list=[[] for _ in range(model_count)],
                labels_list=[[] for _ in range(model_count)],
                weights=[rng.uniform(.5, 4) for _ in range(model_count)],
                iou_thr=.5, skip_box_thr=0., conf_type='avg', allows_overflow=False)
    templates = {(0, 0): [.1, .1, .2, .2], (0, 1): [.4, .4, .5, .5],
                 (1, 0): [.7, .1, .8, .2], (1, 1): [.7, .7, .8, .8]}
    for model in range(model_count):
        for (label, _), box in templates.items():
            for _ in range(rng.randint(0, 4)):
                data['boxes_list'][model].append(box)
                data['scores_list'][model].append(rng.uniform(.1, 1))
                data['labels_list'][model].append(label)
    if not any(data['boxes_list']):
        data['boxes_list'][0].append(templates[(0, 0)])
        data['scores_list'][0].append(.8)
        data['labels_list'][0].append(0)
    return data


def canonical(output):
    boxes, scores, labels = output
    order = sorted(range(len(boxes)), key=lambda i: (int(labels[i]), *boxes[i].tolist()))
    return boxes[order], scores[order], labels[order]


def test_score_bounds_and_overflow_mode_relations(audit):
    rng = random.Random(20260918011)
    bound_violations = 0
    for index in range(500):
        source = make_case(rng)
        results = {}
        for mode in MODES:
            for overflow in (False, True):
                data = copy.deepcopy(source)
                data['conf_type'] = mode
                data['allows_overflow'] = overflow
                audit.source(data)
                output = audit.call(data)
                check_output(output)
                boxes, scores, labels = canonical(output)
                if not overflow:
                    excessive = scores[scores > 1 + ATOL]
                    if len(excessive):
                        bound_violations += 1
                        audit.counts['disabled_overflow_bound_violations'] += 1
                        if len(audit.findings) < 10:
                            audit.findings.append(dict(
                                kind='score_above_one_with_overflow_disabled', index=index,
                                mode=mode, maximum_score=float(excessive.max()),
                                input=source, output=output))
                results[(mode, overflow)] = (boxes, scores, labels)

        for mode in MODES:
            false = results[(mode, False)]
            true = results[(mode, True)]
            assert np.array_equal(false[2], true[2])
            assert np.allclose(false[0], true[0], atol=ATOL, rtol=RTOL)
            if mode == 'avg':
                assert np.all(true[1] + ATOL >= false[1])
                audit.counts['avg_overflow_scores_above_one'] += int(np.any(true[1] > 1 + ATOL))
            else:
                assert np.allclose(false[1], true[1], atol=ATOL, rtol=RTOL)
                assert np.all(true[1] <= 1 + ATOL)
                audit.counts['overflow_ignored_mode_comparisons'] += 1

        if len(audit.samples) < 3:
            audit.samples.append(dict(index=index, model_count=len(source['weights']),
                                      input_boxes=sum(map(len, source['boxes_list'])),
                                      output_counts={mode: len(results[(mode, False)][0])
                                                     for mode in MODES}))
    assert bound_violations == 0, f'{bound_violations} configurations exceeded score 1'
