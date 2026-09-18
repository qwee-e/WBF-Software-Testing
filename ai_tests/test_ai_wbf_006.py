from hypothesis import HealthCheck, given, seed, settings
from ai_tests.support import coverage_examples, map_boxes, map_output, stable_inputs


def mirror(box):
    x1, y1, x2, y2 = box
    return [1 - x2, y1, 1 - x1, y2]


@seed(20260918006)
@settings(max_examples=300, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_horizontal_mirror(audit, data):
    audit.source(data)
    baseline = audit.call(data)
    mirrored = map_boxes(data, mirror)
    audit.compare(data, mirrored, map_output(baseline, mirror), audit.call(mirrored),
                  dict(operation='horizontal_mirror'))
    restored = map_boxes(mirrored, mirror)
    audit.compare(data, restored, baseline, audit.call(restored),
                  dict(operation='double_horizontal_mirror'))
