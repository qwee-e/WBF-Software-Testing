import copy
import random

import numpy as np

from ai_tests.support import MODES


def make_case(rng):
    model_count = rng.randint(3, 6)
    class_count = rng.randint(2, 4)
    cluster_count = rng.randint(2, 3)
    weights = [rng.uniform(.5, 4) for _ in range(model_count)]
    data = dict(boxes_list=[[] for _ in range(model_count)],
                scores_list=[[] for _ in range(model_count)],
                labels_list=[[] for _ in range(model_count)], weights=weights,
                iou_thr=.5, skip_box_thr=0., conf_type='avg', allows_overflow=False)
    clusters = []
    positions = [(.05, .05), (.40, .05), (.75, .05),
                 (.05, .40), (.40, .40), (.75, .40),
                 (.05, .75), (.40, .75), (.75, .75),
                 (.22, .22), (.57, .22), (.22, .57)]
    for label in range(class_count):
        for cluster in range(cluster_count):
            x, y = positions[label * cluster_count + cluster]
            box = [x, y, x + .1, y + .1]
            repeats = [rng.randint(0, 3) for _ in range(model_count)]
            if not any(repeats):
                repeats[rng.randrange(model_count)] = 1
            members = []
            for model, repeat in enumerate(repeats):
                for _ in range(repeat):
                    score = rng.uniform(.1, 1)
                    data['boxes_list'][model].append(box)
                    data['scores_list'][model].append(score)
                    data['labels_list'][model].append(label)
                    members.append((model, score))
            clusters.append(dict(label=label, box=box, members=members))
    return data, clusters


def for_label(data, wanted):
    result = copy.deepcopy(data)
    for model in range(len(data['weights'])):
        keep = [i for i, label in enumerate(data['labels_list'][model]) if label == wanted]
        for key in ('boxes_list', 'scores_list', 'labels_list'):
            result[key][model] = [data[key][model][i] for i in keep]
    return result


def concatenate(outputs):
    return tuple(np.concatenate([output[index] for output in outputs], axis=0)
                 if outputs else np.empty((0, 4) if index == 0 else (0,))
                 for index in range(3))


def expected_output(data, clusters, mode):
    weights = data['weights']
    total_weight = sum(weights)
    boxes, scores, labels = [], [], []
    for cluster in clusters:
        members = cluster['members']
        count = len(members)
        q_value = sum(score * weights[model] for model, score in members)
        repeated_weight = sum(weights[model] for model, _ in members)
        present_weight = sum(weights[model] for model in {model for model, _ in members})
        if mode == 'box_and_model_avg':
            score = (q_value / repeated_weight) * (present_weight / total_weight)
        elif mode == 'absent_model_aware_avg':
            score = q_value / (repeated_weight + total_weight - present_weight)
        elif mode == 'avg':
            score = (q_value / count) * min(len(weights), count) / total_weight
        else:
            score = max(member_score * weights[model] for model, member_score in members) / max(weights)
        boxes.append(cluster['box'])
        scores.append(score)
        labels.append(cluster['label'])
    return np.array(boxes), np.array(scores), np.array(labels)


def test_multiclass_decomposition_and_independent_formulas(audit):
    rng = random.Random(20260918015)
    for index in range(500):
        source, clusters = make_case(rng)
        class_count = len({cluster['label'] for cluster in clusters})
        for mode in MODES:
            data = copy.deepcopy(source)
            data['conf_type'] = mode
            audit.source(data)
            actual = audit.call(data)

            separated = []
            for label in range(class_count):
                one_class = for_label(data, label)
                separated.append(audit.call(one_class))
            union = concatenate(separated)
            audit.compare(data, dict(operation='split_by_class', class_count=class_count),
                          union, actual, dict(operation='class_decomposition', mode=mode))

            formula = expected_output(data, clusters, mode)
            audit.compare(data, dict(operation='independent_formula', mode=mode),
                          formula, actual, dict(operation='formula_check', mode=mode))
            audit.counts['formula_cluster_checks'] += len(clusters)
