import random

from ai_tests.bridge import (BRIDGE_SEED, assert_exact_repeat, bridge_input, permutations,
                             remove_ties, separate_control, shrink_pair)
from ai_tests.support import check_output, same_output


def test_bridge_permutation_search(audit):
    rng = random.Random(BRIDGE_SEED)
    witness = None
    for index in range(150):
        data = bridge_input(rng, index)
        audit.source(data)
        baseline = audit.call(data)
        assert_exact_repeat(baseline, audit.call(data))
        audit.counts['determinism_checks'] += 1
        untied_baseline = audit.call(remove_ties(data))
        separated_baseline = audit.call(separate_control(data))
        sensitive = False
        for changed in permutations(data, rng):
            output = audit.call(changed)
            check_output(output)
            assert_exact_repeat(output, audit.call(changed))
            audit.counts['determinism_checks'] += 1
            audit.counts['permutations_checked'] += 1
            if not same_output(baseline, output):
                sensitive = True
                audit.counts['sensitive_permutations'] += 1
                if witness is None:
                    witness = dict(input=data, permuted_input=changed,
                                   output=baseline, permuted_output=output, scenario_index=index,
                                   classification='algorithm_order_sensitivity_not_automatic_bug')
            # De-tied bridge remains exploratory: it need not satisfy domain S.
            untied = audit.call(remove_ties(changed))
            check_output(untied)
            audit.counts['untied_comparisons'] += 1
            audit.counts['untied_differences'] += int(not same_output(untied_baseline, untied))
            # Strict control has unique weighted scores AND disjoint clusters.
            control = separate_control(changed)
            audit.compare(separate_control(data), control, separated_baseline, audit.call(control),
                          dict(operation='untied_separated_control', scenario_index=index))
        audit.counts['sensitive_scenarios'] += int(sensitive)
    if witness is not None:
        audit.findings.append(witness)

        def shrink_call(data):
            audit.counts['shrink_calls'] += 1
            return audit.call(data)

        left, right, attempts = shrink_pair(witness['input'], witness['permuted_input'], shrink_call)
        audit.counts['shrink_attempts'] += attempts
        output_left, output_right = audit.call(left), audit.call(right)
        assert not same_output(output_left, output_right)
        assert_exact_repeat(output_left, audit.call(left))
        assert_exact_repeat(output_right, audit.call(right))
        audit.counts['replay_calls'] += 4
        audit.findings.append(dict(input=left, permuted_input=right, output=output_left,
                                   permuted_output=output_right, seed=BRIDGE_SEED,
                                   retained_boxes=sum(map(len, left['boxes_list'])),
                                   minimality='1-minimal under synchronized single-box deletion; model slots retained',
                                   classification='algorithm_order_sensitivity_not_automatic_bug'))
    print(f'Bridge observations: {dict(audit.counts)}')
