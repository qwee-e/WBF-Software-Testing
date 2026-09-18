from hypothesis import HealthCheck, given, seed, settings
from ai_tests.support import coverage_examples, model_permutation, rng_for, stable_inputs


@seed(20260918001)
@settings(max_examples=200, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_model_permutation(audit, data):
    audit.source(data)
    expected = audit.call(data)
    rng = rng_for(data, '001')
    identity = tuple(range(len(data['weights'])))
    seen = {identity}
    for attempt in range(100):
        order = list(reversed(identity)) if attempt == 0 else rng.sample(identity, len(identity))
        if tuple(order) in seen:
            continue
        seen.add(tuple(order))
        transformed = model_permutation(data, order)
        actual = audit.call(transformed)
        audit.compare(data, transformed, expected, actual, dict(model_order=order))
        if len(seen) == 11:
            break
