from hypothesis import HealthCheck, given, seed, settings
from ai_tests.support import box_permutation, coverage_examples, digest, rng_for, stable_inputs


@seed(20260918002)
@settings(max_examples=200, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_box_permutation(audit, data):
    audit.source(data)
    expected = audit.call(data)
    rng = rng_for(data, '002')
    seen = {digest(data)}
    for attempt in range(100):
        orders = [list(reversed(range(len(boxes)))) if attempt == 0
                  else rng.sample(range(len(boxes)), len(boxes)) for boxes in data['boxes_list']]
        transformed = box_permutation(data, orders)
        signature = digest(transformed)
        if signature in seen:
            continue
        seen.add(signature)
        audit.compare(data, transformed, expected, audit.call(transformed), dict(box_orders=orders))
        if len(seen) == 11:
            break
