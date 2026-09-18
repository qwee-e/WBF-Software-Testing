"""Seeded bridge topologies and deletion-minimal paired witnesses."""
import copy
import random

import numpy as np

from ai_tests.support import MODES, box_permutation, check_output, digest, model_permutation, same_output

BRIDGE_SEED = 20260918014


def bridge_input(rng, index):
    m = (1, 3, 4)[index % 3]
    weights = [rng.choice([.5, 1., 2., 4.]) for _ in range(m)]
    data = dict(boxes_list=[[] for _ in range(m)], scores_list=[[] for _ in range(m)],
                labels_list=[[] for _ in range(m)], weights=weights,
                iou_thr=rng.uniform(.42, .48), skip_box_thr=0.,
                conf_type=MODES[index % 4], allows_overflow=bool((index // 4) % 2))
    x, y = rng.uniform(.05, .2), rng.uniform(.05, .25)
    width, height = rng.uniform(.15, .25), rng.uniform(.1, .25)
    label = rng.randrange(4)
    for i in range(3):
        model = 0 if m == 1 else (i if m == 3 else rng.randrange(m))
        left = x + .3 * width * i
        data['boxes_list'][model].append([left, y, left + width, y + height])
        data['scores_list'][model].append(.25 / weights[model])
        data['labels_list'][model].append(label)
    for i in range(rng.randint(2, 5)):
        model = rng.randrange(m)
        left = .03 + .15 * i
        data['boxes_list'][model].append([left, .75, left + .06, .82])
        data['scores_list'][model].append((.1 + .005 * i) / weights[model])
        data['labels_list'][model].append(rng.randrange(4))
    return data


def permutations(data, rng, limit=20):
    seen = {digest(data)}
    for _ in range(200):
        model_order = rng.sample(range(len(data['weights'])), len(data['weights']))
        other = model_permutation(data, model_order)
        box_orders = [rng.sample(range(len(boxes)), len(boxes)) for boxes in other['boxes_list']]
        other = box_permutation(other, box_orders)
        signature = digest(other)
        if signature in seen:
            continue
        seen.add(signature)
        yield other
        if len(seen) == limit + 1:
            return


def remove_ties(data):
    other = copy.deepcopy(data)
    # Coordinate identity survives model/box permutations; scores follow records.
    keys = sorted(tuple(box) for model in data['boxes_list'] for box in model)
    ranks = {box: rank for rank, box in enumerate(keys)}
    for m, boxes in enumerate(other['boxes_list']):
        for j, box in enumerate(boxes):
            other['scores_list'][m][j] = (.2 + .01 * ranks[tuple(box)]) / other['weights'][m]
    return other


def separate_control(data):
    """Turn the topology into S: disjoint templates and strictly ordered scores."""
    other = remove_ties(data)
    keys = sorted(tuple(box) for model in data['boxes_list'] for box in model)
    ranks = {box: rank for rank, box in enumerate(keys)}
    for boxes in other['boxes_list']:
        for j, box in enumerate(boxes):
            rank = ranks[tuple(box)]
            x, y = .03 + .22 * (rank % 4), .1 + .35 * (rank // 4)
            boxes[j] = [x, y, x + .08, y + .08]
    return other


def without_box(data, key):
    other = copy.deepcopy(data)
    for m, boxes in enumerate(other['boxes_list']):
        for j, box in enumerate(boxes):
            if tuple(box) == tuple(key):
                for field in ('boxes_list', 'scores_list', 'labels_list'):
                    del other[field][m][j]
                return other
    raise ValueError('Paired record is missing')


def shrink_pair(left, right, evaluate):
    """1-minimal for deletion of corresponding boxes; not globally minimal."""
    left, right = copy.deepcopy(left), copy.deepcopy(right)
    attempts = 0
    while True:
        changed = False
        for key in [tuple(b) for model in left['boxes_list'] for b in model]:
            a, b = without_box(left, key), without_box(right, key)
            attempts += 1
            if not same_output(evaluate(a), evaluate(b)):
                left, right, changed = a, b, True
                break
        if not changed:
            break
    return left, right, attempts


def assert_exact_repeat(first, repeated):
    check_output(first)
    check_output(repeated)
    assert all(np.array_equal(a, b) for a, b in zip(first, repeated)), 'Same input is not deterministic'
