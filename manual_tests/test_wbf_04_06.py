"""Tests 04 and 06 with fixed inputs and precomputed expected outputs."""
import json
import warnings
from pathlib import Path

import numpy as np
import pytest

from ensemble_boxes import weighted_boxes_fusion


@pytest.mark.parametrize("case_id", ["WBF-04", "WBF-06"])
def test_non_fusion(case_id):
    case = json.loads((Path(__file__).resolve().parents[1] /
                       "test_data" / f"{case_id}.json").read_text())
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        boxes, scores, labels = weighted_boxes_fusion(**case["input"])
    print(json.dumps({
        "case_id": case_id,
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
