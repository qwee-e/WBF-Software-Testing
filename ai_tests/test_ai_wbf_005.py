import numpy as np
from hypothesis import HealthCheck, given, seed, settings
from ai_tests.support import coverage_examples, map_boxes, map_output, rng_for, stable_inputs


@seed(20260918005)
@settings(max_examples=300, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_uniform_scaling(audit, data):
    audit.source(data)
    baseline = audit.call(data)
    maximum = max(max(box) for model in data['boxes_list'] for box in model)
    upper = min(2., .98 / maximum)
    rng = rng_for(data, '005')
    # Explicitly exercise shrinking and enlargement, not just three random factors.
    factors = [rng.uniform(.5, .9), rng.uniform(1.05, upper), rng.uniform(.5, upper)]
    for factor in factors:
        transform = lambda box: np.asarray(box) * factor
        transformed = map_boxes(data, transform)
        audit.compare(data, transformed, map_output(baseline, transform), audit.call(transformed),
                      dict(uniform_scale=factor))
