"""Fixed-input WBF contract test with recorded observations."""
import json
import warnings
from pathlib import Path
import numpy as np
from ensemble_boxes import weighted_boxes_fusion


def test_case():
    case = json.loads((Path(__file__).resolve().parents[1] / "test_data" / "WBF-30.json").read_text())
    expected = case["expected"]
    error = None
    result = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = weighted_boxes_fusion(**case["input"])
        except (Exception, SystemExit) as exc:
            error = exc
    observation = {"case_id": case["case_id"], "warnings": [str(w.message) for w in caught],
                   "exception": None if error is None else type(error).__name__,
                   "exception_message": None if error is None else str(error)}
    if result is not None:
        observation.update(zip(("boxes", "scores", "labels"), [a.tolist() for a in result]))
        observation["shapes"] = [list(a.shape) for a in result]
    print(json.dumps(observation, ensure_ascii=False))
    if expected["contract"] == "value_error":
        assert isinstance(error, ValueError), f"Expected ValueError; observed {observation}"
        return
    assert error is None, observation
    boxes, scores, labels = result
    assert all(np.isfinite(a).all() for a in result), observation
    if expected["contract"] == "bounded":
        assert boxes.shape == (1, 4)
        np.testing.assert_allclose(boxes, [[.1, .1, .5, .5]], rtol=0, atol=1e-6)
        np.testing.assert_array_equal(labels, [1])
        assert scores.shape == (1,)
        assert ((scores >= 0) & (scores <= 1)).all(), observation
        return
    count = len(expected["scores"])
    assert boxes.shape == (count, 4)
    assert scores.shape == labels.shape == (count,)
    np.testing.assert_allclose(boxes, np.asarray(expected["boxes"]).reshape(count, 4), rtol=0, atol=1e-6)
    np.testing.assert_allclose(scores, expected["scores"], rtol=0, atol=1e-6)
    np.testing.assert_array_equal(labels, expected["labels"])
    assert observation["warnings"] == expected["warnings"]
