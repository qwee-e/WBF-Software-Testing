import random
from collections import Counter

import numpy as np

from ai_tests.support import MODES, check_output


def make_case(rng, index):
    model_count = index % 9
    boxes_list, scores_list, labels_list = [], [], []
    for model in range(model_count):
        count = rng.randint(0, 50)
        boxes, scores, labels = [], [], []
        for _ in range(count):
            x1, y1 = rng.uniform(0, .97), rng.uniform(0, .97)
            x2, y2 = rng.uniform(x1 + .001, 1), rng.uniform(y1 + .001, 1)
            boxes.append([x1, y1, x2, y2])
            scores.append(rng.uniform(.01, 1))
            labels.append(rng.randrange(10))
        boxes_list.append(boxes)
        scores_list.append(scores)
        labels_list.append(labels)
    return dict(boxes_list=boxes_list, scores_list=scores_list, labels_list=labels_list,
                weights=[rng.uniform(.5, 4) for _ in range(model_count)],
                iou_thr=rng.uniform(.1, .9), skip_box_thr=rng.uniform(0, .9),
                conf_type=MODES[(index // 2) % len(MODES)],
                allows_overflow=bool(index % 2))


def test_output_structure_source_and_count_invariants(audit):
    rng = random.Random(20260918010)
    for index in range(800):
        data = make_case(rng, index)
        audit.source(data)
        output = audit.call(data)
        check_output(output)
        boxes, scores, labels = output

        valid = Counter(label for model_scores, model_labels in
                        zip(data['scores_list'], data['labels_list'])
                        for score, label in zip(model_scores, model_labels)
                        if score >= data['skip_box_thr'])
        observed = Counter(int(label) for label in labels)
        assert len(boxes) <= sum(valid.values())
        assert set(observed) <= set(valid)
        assert all(observed[label] <= valid[label] for label in observed)
        assert np.all(np.diff(scores) <= 0), 'scores are not descending'

        audit.counts['valid_input_boxes'] += sum(valid.values())
        audit.counts['output_boxes'] += len(boxes)
        audit.counts['zero_model_inputs'] += int(len(data['boxes_list']) == 0)
        if len(audit.samples) < 3:
            audit.samples.append(dict(index=index, model_count=len(data['boxes_list']),
                                      valid_input_boxes=sum(valid.values()),
                                      output_boxes=len(boxes), labels=sorted(observed)))
