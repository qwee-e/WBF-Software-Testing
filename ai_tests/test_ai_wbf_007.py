import copy

import numpy as np
from hypothesis import HealthCheck, given, seed, settings

from ai_tests.support import check_output, coverage_examples, map_output, rng_for, stable_inputs


def rename_input(data, mapping):
    renamed = copy.deepcopy(data)
    renamed['labels_list'] = [[mapping[label] for label in labels]
                              for labels in data['labels_list']]
    return renamed


@seed(20260918007)
@settings(max_examples=300, deadline=None, database=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=stable_inputs())
@coverage_examples
def test_bijective_label_renaming(audit, data):
    audit.source(data)
    baseline = audit.call(data)
    labels = sorted({label for model in data['labels_list'] for label in model})
    rng = rng_for(data, '007-label-map')
    targets = rng.sample(range(10, 100), len(labels))
    mapping = dict(zip(labels, targets))
    renamed = rename_input(data, mapping)
    expected = map_output(baseline, lambda box: box)
    expected = (expected[0], expected[1], np.array([mapping[int(label)] for label in expected[2]]))
    audit.compare(data, renamed, expected, audit.call(renamed),
                  dict(operation='bijective_label_rename', mapping=mapping))

    inverse = {target: source for source, target in mapping.items()}
    restored = rename_input(renamed, inverse)
    audit.compare(data, restored, baseline, audit.call(restored),
                  dict(operation='inverse_label_restore', inverse_mapping=inverse))

    if audit.counts['source_examples'] <= 50:
        offset = rng.randrange(-64, 65)
        large_labels = [2 ** 24 + offset, 2 ** 24 + offset + 1]
        exploration = dict(
            boxes_list=[[[.1, .1, .2, .2], [.6, .6, .7, .7]],
                        [[.101, .1, .201, .2], [.601, .6, .701, .7]]],
            scores_list=[[.9, .8], [.7, .6]], labels_list=[large_labels, large_labels],
            weights=[1., 1.], iou_thr=.5, skip_box_thr=0.,
            conf_type='avg', allows_overflow=False)
        audit.counts['large_label_explorations'] += 1
        output = audit.call(exploration)
        check_output(output)
        observed = {int(label) for label in output[2]}
        expected_labels = set(large_labels)
        if observed != expected_labels:
            audit.counts['large_label_precision_differences'] += 1
            if len(audit.findings) < 10:
                audit.findings.append(dict(kind='exploratory_label_precision',
                                           input_labels=large_labels,
                                           expected=sorted(expected_labels),
                                           observed=sorted(observed)))
