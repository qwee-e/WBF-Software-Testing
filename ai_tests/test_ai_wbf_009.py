from hypothesis import HealthCheck, given, seed, settings, strategies as st

from ai_tests.support import MODES, check_output, coverage_examples


@st.composite
def legal_inputs(draw):
    model_count = draw(st.integers(1, 6))
    boxes_list, scores_list, labels_list = [], [], []
    for _ in range(model_count):
        count = draw(st.integers(0, 20))
        x1 = draw(st.lists(st.integers(0, 89), min_size=count, max_size=count))
        y1 = draw(st.lists(st.integers(0, 89), min_size=count, max_size=count))
        widths = draw(st.lists(st.integers(1, 100), min_size=count, max_size=count))
        heights = draw(st.lists(st.integers(1, 100), min_size=count, max_size=count))
        boxes = []
        for x, y, width, height in zip(x1, y1, widths, heights):
            left, top = x / 100, y / 100
            boxes.append([left, top, left + min(width / 100, 1 - left),
                          top + min(height / 100, 1 - top)])
        boxes_list.append(boxes)
        scores_list.append(draw(st.lists(st.integers(1, 100).map(lambda v: v / 100),
                                         min_size=count, max_size=count)))
        labels_list.append(draw(st.lists(st.integers(0, 9), min_size=count, max_size=count)))
    return dict(boxes_list=boxes_list, scores_list=scores_list, labels_list=labels_list,
                weights=draw(st.lists(st.sampled_from([.5, 1., 2., 4.]),
                                      min_size=model_count, max_size=model_count)),
                iou_thr=draw(st.integers(10, 90).map(lambda v: v / 100)),
                skip_box_thr=draw(st.integers(0, 90).map(lambda v: v / 100)),
                conf_type=draw(st.sampled_from(MODES)), allows_overflow=draw(st.booleans()))


@seed(20260918009)
@settings(max_examples=800, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=legal_inputs())
@coverage_examples
def test_random_legal_output_validity(audit, data):
    audit.source(data)
    output = audit.call(data)
    check_output(output)
    audit.counts['output_boxes'] += len(output[0])
    audit.counts['empty_outputs'] += int(len(output[0]) == 0)
