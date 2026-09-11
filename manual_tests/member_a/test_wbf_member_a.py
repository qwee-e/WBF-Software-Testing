"""Member A's independently specified examples; expected values precede execution."""
import json
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[2] / "test_data/member_a"


def case(number):
    return json.loads((DATA / f"WBF-UT-{number:03d}.json").read_text(encoding="utf-8"))


def assert_output(probe, params, expected, scenario="spreadsheet_input", warning=None):
    result, error, record = probe(params, scenario)
    assert error is None, f"Unexpected {type(error).__name__}: {error}"
    boxes, scores, labels = result
    n = len(expected["boxes"])
    assert boxes.shape == (n, 4)
    assert scores.shape == labels.shape == (n,)
    assert all(np.isfinite(a).all() for a in result), "Output contains NaN or Inf"
    np.testing.assert_allclose(boxes, np.asarray(expected["boxes"]).reshape(n, 4), rtol=1e-6, atol=1e-7)
    np.testing.assert_allclose(scores, expected["scores"], rtol=1e-6, atol=1e-7)
    np.testing.assert_array_equal(labels, expected["labels"])
    assert np.all(scores[:-1] >= scores[1:]), "Scores must be descending"
    if warning:
        assert any(w["category"] == "UserWarning" and warning in w["message"] for w in record["warnings"])
    else:
        assert not record["warnings"], record["warnings"]
    return result


def test_001__single_valid_box(probe):
    spec = case(1)
    assert_output(probe, spec["input"], spec["expected"])


def test_003__disjoint_same_class(probe):
    spec = case(3)
    assert_output(probe, spec["input"], spec["expected"])
