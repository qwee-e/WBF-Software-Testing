"""WBF-08: zero IoU threshold with touching and disjoint boxes."""
import json
from pathlib import Path
import warnings

import numpy as np
import pytest

from ensemble_boxes import weighted_boxes_fusion


@pytest.mark.parametrize("scenario", ["edge_touch", "disjoint"])
def test_wbf_08_zero_threshold(scenario):
    data = json.loads((Path(__file__).resolve().parents[1] /
                       "test_data/WBF-08.json").read_text())
    case = next(item for item in data["scenarios"] if item["scenario"] == scenario)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        boxes, scores, labels = weighted_boxes_fusion(**case["input"])
    print(json.dumps({
        "case_id": "WBF-08", "scenario": scenario,
        "boxes": boxes.tolist(), "scores": scores.tolist(),
        "labels": labels.tolist(),
        "shapes": [list(a.shape) for a in (boxes, scores, labels)],
        "warnings": [str(w.message) for w in caught],
    }, ensure_ascii=False))
    assert boxes.shape == (2, 4)
    assert scores.shape == (2,)
    assert labels.shape == (2,)
    np.testing.assert_allclose(boxes, case["expected"]["boxes"], rtol=0, atol=1e-6)
    np.testing.assert_allclose(scores, case["expected"]["scores"], rtol=0, atol=1e-6)
    np.testing.assert_array_equal(labels, case["expected"]["labels"])
    assert not caught, "合法输入不应产生警告"
