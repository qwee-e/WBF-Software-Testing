"""WBF-02: AI-assisted scenario; expected values calculated before execution."""
import json
import warnings

import numpy as np

from ensemble_boxes import weighted_boxes_fusion


def test_wbf_02_identical_boxes():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        boxes, scores, labels = weighted_boxes_fusion(
            boxes_list=[[[0.1, 0.1, 0.5, 0.5]], [[0.1, 0.1, 0.5, 0.5]]],
            scores_list=[[0.9], [0.8]],
            labels_list=[[1], [1]],
            weights=[1, 1],
            iou_thr=0.55,
            skip_box_thr=0.0,
            conf_type="avg",
            allows_overflow=False,
        )
    print(json.dumps({
        "boxes": boxes.tolist(), "scores": scores.tolist(),
        "labels": labels.tolist(),
        "shapes": [list(a.shape) for a in (boxes, scores, labels)],
        "warnings": [str(w.message) for w in caught],
    }, ensure_ascii=False))

    assert boxes.shape == (1, 4)
    assert scores.shape == (1,)
    assert labels.shape == (1,)
    np.testing.assert_allclose(boxes, [[0.1, 0.1, 0.5, 0.5]], rtol=0, atol=1e-6)
    np.testing.assert_allclose(scores, [0.85], rtol=0, atol=1e-6)
    np.testing.assert_array_equal(labels, [1])
    assert not caught, "合法输入不应产生警告"
