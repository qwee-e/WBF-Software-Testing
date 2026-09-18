import copy
from hypothesis import HealthCheck, given, seed, settings
from ai_tests.support import coverage_examples, rng_for, stable_inputs


@seed(20260918008)
@settings(max_examples=300, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_filtered_noise_injection(audit, data):
    data = copy.deepcopy(data)
    data['skip_box_thr'] = max(.05, data['skip_box_thr'])
    audit.source(data)
    expected = audit.call(data)
    rng = rng_for(data, '008')
    # Include small and large injections; no extra model slot or weight is added.
    for amount in (1, rng.randint(2, 99), 100):
        transformed = copy.deepcopy(data)
        for _ in range(amount):
            model = rng.randrange(len(data['weights']))
            x, y = rng.uniform(0, .9), rng.uniform(0, .9)
            box = [x, y, x + rng.uniform(.01, 1 - x), y + rng.uniform(.01, 1 - y)]
            score = rng.uniform(0, .9 * data['skip_box_thr'])
            transformed['boxes_list'][model].append(box)
            transformed['scores_list'][model].append(score)
            transformed['labels_list'][model].append(rng.randrange(10))
        audit.counts['injected_boxes'] += amount
        audit.compare(data, transformed, expected, audit.call(transformed),
                      dict(injected_boxes=amount, score_upper_exclusive=data['skip_box_thr']))
