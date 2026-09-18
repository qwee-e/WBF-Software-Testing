"""Structure-preserving Fuzz generators, independent properties and minimization."""
import contextlib
import copy
import io
import warnings

import numpy as np

from ai_tests.support import ATOL, MODES, box_permutation, model_permutation

FUZZ_SEEDS = (20260918016, 20260918017, 20260918018, 20260918019, 20260918020)
MUTATIONS = ('model_count', 'duplicate_detection', 'dense_overlap', 'empty_model',
             'label_bijection', 'permutation', 'near_threshold', 'numeric_scale',
             'filter_and_mode', 'box_count')


def random_box(rng):
    x, y = rng.uniform(0, .95), rng.uniform(0, .95)
    return [x, y, rng.uniform(x + .02, 1), rng.uniform(y + .02, 1)]


def add_record(data, model, box, score, label):
    data['boxes_list'][model].append(list(box))
    data['scores_list'][model].append(float(score))
    data['labels_list'][model].append(int(label))


def delete_record(data, model, index):
    other = copy.deepcopy(data)
    for key in ('boxes_list', 'scores_list', 'labels_list'):
        del other[key][model][index]
    return other


def delete_model(data, model):
    other = copy.deepcopy(data)
    for key in ('boxes_list', 'scores_list', 'labels_list', 'weights'):
        del other[key][model]
    return other


def fresh_input(rng):
    m = rng.randint(1, 6)
    result = dict(boxes_list=[[] for _ in range(m)], scores_list=[[] for _ in range(m)],
                  labels_list=[[] for _ in range(m)], weights=[rng.choice([.5, 1., 2., 4.]) for _ in range(m)],
                  iou_thr=rng.uniform(.1, .9), skip_box_thr=rng.choice([0., .05, .3, .8]),
                  conf_type=rng.choice(MODES), allows_overflow=bool(rng.randrange(2)))
    template = random_box(rng)
    for model in range(m):
        for _ in range(rng.randint(0, 10)):
            box = template if rng.random() < .5 else random_box(rng)
            add_record(result, model, box, rng.uniform(.01, 1), rng.randrange(4))
    return result


def mutate(data, rng, operation):
    other = copy.deepcopy(data)
    m = len(other['weights'])
    model = rng.randrange(m)
    if operation == 'model_count':
        if m > 1 and (m == 6 or rng.random() < .5):
            other = delete_model(other, model)
        else:
            for key in ('boxes_list', 'scores_list', 'labels_list'):
                other[key].append([])
            other['weights'].append(rng.choice([.5, 1., 2., 4.]))
            for _ in range(rng.randint(0, 5)):
                add_record(other, m, random_box(rng), rng.uniform(.01, 1), rng.randrange(4))
    elif operation == 'duplicate_detection':
        if not other['boxes_list'][model]:
            add_record(other, model, random_box(rng), rng.uniform(.8, 1), rng.randrange(4))
        j = rng.randrange(len(other['boxes_list'][model]))
        for _ in range(min(rng.randint(1, 5), 20 - len(other['boxes_list'][model]))):
            add_record(other, model, other['boxes_list'][model][j],
                       other['scores_list'][model][j], other['labels_list'][model][j])
    elif operation == 'dense_overlap':
        template = random_box(rng)
        label = rng.randrange(4)
        for k, boxes in enumerate(other['boxes_list']):
            for j in range(len(boxes)):
                boxes[j] = list(template)
                other['labels_list'][k][j] = label
    elif operation == 'empty_model':
        for key in ('boxes_list', 'scores_list', 'labels_list'):
            other[key][model] = []
    elif operation == 'label_bijection':
        mapping = rng.sample(range(10), 10)
        other['labels_list'] = [[mapping[label] for label in labels] for labels in other['labels_list']]
    elif operation == 'permutation':
        other = model_permutation(other, rng.sample(range(m), m))
        other = box_permutation(other, [rng.sample(range(len(boxes)), len(boxes))
                                       for boxes in other['boxes_list']])
    elif operation == 'near_threshold':
        threshold = rng.uniform(.1, .9)
        target_iou = threshold + rng.choice([-1e-8, 0., 1e-8])
        width = rng.uniform(.1, .25)
        shift = width * (1 - target_iou) / (1 + target_iou)
        x, y = rng.uniform(.05, .3), rng.uniform(.05, .5)
        other['iou_thr'] = threshold
        for k in range(2):
            slot = (model + k) % m
            if len(other['boxes_list'][slot]) >= 20:
                other = delete_record(other, slot, 0)
            add_record(other, slot, [x + k * shift, y, x + width + k * shift, y + .2],
                       rng.uniform(.5, 1), 0)
    elif operation == 'numeric_scale':
        other['weights'] = [rng.choice([1e-6, .001, 1., 1000., 1e6]) for _ in range(m)]
        other['scores_list'] = [[10 ** rng.uniform(-8, 0) for _ in boxes] for boxes in other['boxes_list']]
    elif operation == 'filter_and_mode':
        other['skip_box_thr'] = rng.uniform(0, .9)
        other['conf_type'] = rng.choice(MODES)
        other['allows_overflow'] = bool(rng.randrange(2))
    elif operation == 'box_count':
        if other['boxes_list'][model] and rng.random() < .5:
            other = delete_record(other, model, rng.randrange(len(other['boxes_list'][model])))
        elif len(other['boxes_list'][model]) < 20:
            add_record(other, model, random_box(rng), rng.uniform(.01, 1), rng.randrange(10))
    else:
        raise ValueError(operation)
    return other


def extreme_weights(data, rng):
    other = copy.deepcopy(data)
    other['weights'] = [rng.choice([1e-100, 1., 1e200]) for _ in other['weights']]
    other['skip_box_thr'] = 0.
    # Guarantee at least two surviving records in a model to exercise float32 accumulation.
    model = rng.randrange(len(other['weights']))
    other['weights'][model] = rng.choice([1e-100, 1e200])
    other['boxes_list'][model] = [[.2, .2, .5, .5], [.2, .2, .5, .5]]
    other['scores_list'][model] = [.8, .9]
    other['labels_list'][model] = [0, 0]
    return other


def valid_input(data, bucket='main'):
    try:
        m = len(data['weights'])
        if not 1 <= m <= 6 or data['conf_type'] not in MODES:
            return False
        if any(len(data[key]) != m for key in ('boxes_list', 'scores_list', 'labels_list')):
            return False
        if not 0 <= data['skip_box_thr'] <= .9 or not .1 <= data['iou_thr'] <= .9:
            return False
        for boxes, scores, labels, weight in zip(data['boxes_list'], data['scores_list'],
                                                 data['labels_list'], data['weights']):
            if not np.isfinite(weight) or weight <= 0 or (bucket == 'main' and not 1e-6 <= weight <= 1e6):
                return False
            if not len(boxes) == len(scores) == len(labels) or len(boxes) > 20:
                return False
            for box, score, label in zip(boxes, scores, labels):
                if len(box) != 4 or not np.isfinite(box).all() or not 1e-8 <= score <= 1:
                    return False
                if not 0 <= box[0] < box[2] <= 1 or not 0 <= box[1] < box[3] <= 1:
                    return False
                if min(box[2] - box[0], box[3] - box[1]) < .01:
                    return False
                if not isinstance(label, int) or not 0 <= label <= 9:
                    return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def observe(data, call):
    """Independent structural properties; no WBF internal helpers as oracle."""
    captured = io.StringIO()
    output = None
    exception = None
    with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(captured):
        warnings.simplefilter('always')
        try:
            output = call(data)
        except (Exception, SystemExit) as exc:
            exception = dict(type=type(exc).__name__, message=str(exc))
    report = dict(output=output, exception=exception, warnings=sorted({str(w.message) for w in caught}),
                  stdout=captured.getvalue(), violations=[])
    issues = report['violations']
    if exception:
        issues.append('exception')
        return report
    if not isinstance(output, (tuple, list)) or len(output) != 3:
        issues.append('shape')
        return report
    boxes, scores, labels = map(np.asarray, output)
    if boxes.ndim != 2 or boxes.shape[1:] != (4,) or scores.shape != (len(boxes),) or labels.shape != scores.shape:
        issues.append('shape')
        return report
    if not all(np.isfinite(a).all() for a in (boxes, scores, labels)):
        issues.append('nonfinite')
        return report
    if (boxes < -ATOL).any() or (boxes > 1 + ATOL).any() or (boxes[:, 2:] <= boxes[:, :2]).any():
        issues.append('geometry')
    eligible_labels = {label for scores_in, labels_in in zip(data['scores_list'], data['labels_list'])
                       for score, label in zip(scores_in, labels_in) if score >= data['skip_box_thr']}
    if not set(labels.tolist()) <= eligible_labels:
        issues.append('label_source')
    if (scores < -ATOL).any():
        issues.append('negative_score')
    # avg+True explicitly permits scores > 1; do not misreport it.
    if not (data['conf_type'] == 'avg' and data['allows_overflow']) and (scores > 1 + ATOL).any():
        issues.append('score_upper')
    return report


def classify(bucket, issue, data):
    if bucket == 'exploratory':
        return 'exploratory_numeric_risk_requires_review'
    if issue == 'score_upper' and data['conf_type'] == 'avg' and not data['allows_overflow']:
        return 'known_module1_score_overflow'
    return 'new_candidate_requires_review'


def minimize(data, bucket, issue, evaluate):
    """Delete records and models to a fixed point; preserve the same violation."""
    current = copy.deepcopy(data)
    attempts = 0
    while True:
        reduced = False
        candidates = [delete_record(current, m, j) for m, boxes in enumerate(current['boxes_list'])
                      for j in range(len(boxes))]
        if len(current['weights']) > 1:
            candidates.extend(delete_model(current, m) for m in range(len(current['weights'])))
        for candidate in candidates:
            if not valid_input(candidate, bucket):
                continue
            attempts += 1
            if issue in evaluate(candidate)['violations']:
                current, reduced = candidate, True
                break
        if not reduced:
            return current, attempts
