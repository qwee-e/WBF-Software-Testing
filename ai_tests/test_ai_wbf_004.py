import numpy as np
from hypothesis import HealthCheck, given, seed, settings
from ai_tests.support import coverage_examples, map_boxes, map_output, rng_for, stable_inputs


@seed(20260918004)
@settings(max_examples=300, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_translation(audit, data):
    audit.source(data)
    baseline = audit.call(data)
    boxes = np.array([box for model in data['boxes_list'] for box in model])
    low = -boxes[:, :2].min(axis=0) + .01
    high = 1 - boxes[:, 2:].max(axis=0) - .01
    rng = rng_for(data, '004')
    for _ in range(3):
        dx, dy = [rng.uniform(a, b) for a, b in zip(low, high)]
        offset = np.array([dx, dy, dx, dy])
        transform = lambda box: np.asarray(box) + offset
        transformed = map_boxes(data, transform)
        audit.compare(data, transformed, map_output(baseline, transform), audit.call(transformed),
                      dict(dx=dx, dy=dy))
