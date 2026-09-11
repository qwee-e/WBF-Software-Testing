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


def test_005__overlap_above_threshold(probe):
    spec = case(5)
    assert_output(probe, spec["input"], spec["expected"])


def test_007__exact_iou_boundary_and_neighbors(probe):
    spec = case(7)
    # Retain the supplied rounded coordinates; they are just below 0.55.
    assert_output(probe, spec["input"], spec["expected"])
    # Supplemental boxes have intersection 0.5, union 1: IoU exactly 0.5.
    for threshold, expected, name in (
        (0.5, spec["supplemental_unfused"], "exact_iou_equals_threshold"),
        (float(np.nextafter(0.5, 0.0)), spec["supplemental_fused"], "threshold_one_float_below_iou"),
        (float(np.nextafter(0.5, 1.0)), spec["supplemental_unfused"], "threshold_one_float_above_iou"),
    ):
        params = dict(spec["supplemental_input"], iou_thr=threshold)
        assert_output(probe, params, expected, name)


def test_009__iou_threshold_one(probe):
    spec = case(9)
    assert_output(probe, spec["input"], spec["expected"])


def test_011__score_below_filter(probe):
    spec = case(11)
    assert_output(probe, spec["input"], spec["expected"])


def test_013__coordinate_endpoints_zero_one(probe):
    spec = case(13)
    assert_output(probe, spec["input"], spec["expected"])


def test_015__reversed_y_coordinates(probe):
    spec = case(15)
    assert_output(probe, spec["input"], spec["expected"], warning="Y2 < Y1")


def test_017__coordinate_above_one(probe):
    spec = case(17)
    assert_output(probe, spec["input"], spec["expected"], warning="X2 > 1")


def test_019__empty_model_list(probe):
    spec = case(19)
    assert_output(probe, spec["input"], spec["expected"])


def test_021__default_weights_equal_explicit_ones(probe):
    spec = case(21)
    default = assert_output(probe, spec["input"], spec["expected"])
    explicit = assert_output(probe, dict(spec["input"], weights=[1, 1]), spec["expected"], "explicit_unit_weights")
    for actual, reference in zip(default, explicit):
        np.testing.assert_allclose(actual, reference, rtol=1e-6, atol=1e-7)


def test_023__mismatched_scores_raise_value_error(probe):
    spec = case(23)
    result, error, record = probe(spec["input"])
    assert isinstance(error, ValueError), (
        f"Proposed robustness contract requires ValueError, got {type(error).__name__}; "
        f"stdout={record['stdout']!r}"
    )
    assert str(error), "Validation error should explain the mismatch"
    assert result is None


def test_025__three_coordinates_raise_value_error(probe):
    spec = case(25)
    result, error, record = probe(spec["input"])
    assert isinstance(error, ValueError), (
        f"Proposed robustness contract requires ValueError, got {type(error).__name__}: {error}"
    )
    assert str(error), "Validation error should explain the invalid box dimensions"
    assert result is None


def test_026__zero_scores_must_not_produce_nan(probe):
    spec = case(26)
    result, error, record = probe(spec["input"])
    if isinstance(error, ValueError):
        assert str(error), "Explicit rejection should explain zero contribution"
        return
    assert error is None, f"Unexpected {type(error).__name__}: {error}"
    boxes, scores, labels = result
    assert boxes.ndim == 2 and boxes.shape[1] == 4
    assert scores.shape == labels.shape == (len(boxes),)
    assert all(np.isfinite(a).all() for a in result), (
        f"Zero-score fusion must not return NaN/Inf; boxes={boxes.tolist()}, scores={scores.tolist()}"
    )
    assert np.all((boxes >= 0) & (boxes <= 1))
    assert np.all(boxes[:, 2] > boxes[:, 0]) and np.all(boxes[:, 3] > boxes[:, 1])
    assert np.all((scores >= 0) & (scores <= 1))
    assert np.all(labels == 1)


def test_029__max_mode_weighted_coordinates_and_score(probe):
    spec = case(29)
    assert_output(probe, spec["input"], spec["expected"])
