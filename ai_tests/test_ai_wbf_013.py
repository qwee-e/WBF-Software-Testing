import copy
import random

from ai_tests.support import MODES


def make_case(rng, index):
    model_count = rng.randint(2, 6)
    representatives = ([.001, 1., 1000.], [.01, 100.], [1e-6, 1., 1e6])
    if index < len(representatives):
        base = list(representatives[index])
        weights = (base * model_count)[:model_count]
    else:
        exponents = [rng.uniform(-6, 6) for _ in range(model_count)]
        weights = [10 ** exponent for exponent in exponents]
    boxes_list, scores_list, labels_list = [], [], []
    templates = [([.1, .1, .2, .2], 0), ([.5, .5, .6, .6], 1)]
    for model in range(model_count):
        boxes, scores, labels = [], [], []
        for box, label in templates:
            jitter = rng.uniform(-.001, .001)
            boxes.append([box[0] + jitter, box[1], box[2] + jitter, box[3]])
            scores.append(rng.uniform(.1, 1))
            labels.append(label)
        boxes_list.append(boxes)
        scores_list.append(scores)
        labels_list.append(labels)
    return dict(boxes_list=boxes_list, scores_list=scores_list, labels_list=labels_list,
                weights=weights, iou_thr=.5, skip_box_thr=0.,
                conf_type=MODES[index % 4], allows_overflow=False)


def test_cross_magnitude_weight_normalization(audit):
    rng = random.Random(20260918013)
    for index in range(500):
        data = make_case(rng, index)
        audit.source(data)
        baseline = audit.call(data)
        maximum = max(data['weights'])
        transformed = copy.deepcopy(data)
        transformed['weights'] = [weight / maximum for weight in data['weights']]
        assert all(weight > 0 for weight in data['weights'])
        assert all(weight > 0 for weight in transformed['weights'])
        audit.compare(data, transformed, baseline, audit.call(transformed),
                      dict(operation='divide_weights_by_maximum', maximum=maximum,
                           ratio=max(data['weights']) / min(data['weights'])))
