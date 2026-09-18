"""AI-WBF-003: common scaling of all model weights is invariant."""

from copy import deepcopy
import random

import numpy as np
import pytest

from ensemble_boxes import weighted_boxes_fusion


CONF_TYPES = (
    "avg",
    "max",
    "box_and_model_avg",
    "absent_model_aware_avg",
)


def build_case(seed):
    """Create separated clusters whose membership stays far from the IoU threshold."""
    rng = random.Random(seed)
    model_count = rng.randint(2, 6)
    weights = [rng.uniform(0.5, 4.0) for _ in range(model_count)]
    templates = (
        (0, (0.08, 0.08, 0.28, 0.28)),
        (0, (0.62, 0.08, 0.82, 0.28)),
        (1, (0.08, 0.62, 0.28, 0.82)),
        (1, (0.62, 0.62, 0.82, 0.82)),
    )
    boxes_list = [[] for _ in range(model_count)]
    scores_list = [[] for _ in range(model_count)]
    labels_list = [[] for _ in range(model_count)]

    for cluster_index, (label, template) in enumerate(templates):
        contributors = [m for m in range(model_count) if rng.random() < 0.72]
        if not contributors:
            contributors = [rng.randrange(model_count)]
        for model_index in contributors:
            dx = rng.uniform(-0.006, 0.006)
            dy = rng.uniform(-0.006, 0.006)
            x1, y1, x2, y2 = template
            boxes_list[model_index].append([x1 + dx, y1 + dy, x2 + dx, y2 + dy])
            score = 0.97 - 0.05 * cluster_index - 0.007 * model_index - rng.uniform(0.0, 0.002)
            scores_list[model_index].append(score)
            labels_list[model_index].append(label)

    exponent = rng.randint(-10, 10)
    return {
        "boxes_list": boxes_list,
        "scores_list": scores_list,
        "labels_list": labels_list,
        "weights": weights,
        "iou_thr": 0.55,
        "skip_box_thr": 0.0,
        "allows_overflow": False,
    }, 2.0 ** exponent


def canonical(result):
    boxes, scores, labels = result
    assert boxes.ndim == 2 and boxes.shape[1] == 4
    assert scores.shape == labels.shape == (len(boxes),)
    assert all(np.isfinite(values).all() for values in result)
    records = [(int(label), *box.tolist(), float(score))
               for box, score, label in zip(boxes, scores, labels)]
    return np.asarray(sorted(records), dtype=np.float64)


@pytest.mark.parametrize("conf_type", CONF_TYPES)
def test_ai_wbf_003_common_weight_scaling(conf_type):
    max_box_error = 0.0
    max_score_error = 0.0
    mode_offset = CONF_TYPES.index(conf_type) * 10_000
    for case_index in range(100):
        params, scale = build_case(30_000 + mode_offset + case_index)
        params["conf_type"] = conf_type
        scaled = deepcopy(params)
        scaled["weights"] = [weight * scale for weight in params["weights"]]

        baseline = canonical(weighted_boxes_fusion(**params))
        transformed = canonical(weighted_boxes_fusion(**scaled))
        assert baseline.shape == transformed.shape
        np.testing.assert_array_equal(baseline[:, 0], transformed[:, 0])
        np.testing.assert_allclose(baseline[:, 1:5], transformed[:, 1:5], rtol=1e-5, atol=1e-6)
        np.testing.assert_allclose(baseline[:, 5], transformed[:, 5], rtol=1e-5, atol=1e-6)
        max_box_error = max(max_box_error, float(np.max(np.abs(baseline[:, 1:5] - transformed[:, 1:5]))))
        max_score_error = max(max_score_error, float(np.max(np.abs(baseline[:, 5] - transformed[:, 5]))))

    print({"case_id": "AI-WBF-003", "conf_type": conf_type,
           "source_cases": 100, "max_box_error": max_box_error,
           "max_score_error": max_score_error})
