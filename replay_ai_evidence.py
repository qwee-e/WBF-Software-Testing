"""Replay a stored AI observation without regenerating the entire search."""
import argparse
import json
from pathlib import Path

from ai_tests.support import json_safe, same_output
from ensemble_boxes.ensemble_boxes_wbf import weighted_boxes_fusion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--finding', type=int, default=-1, help='findings array index; default last')
    args = parser.parse_args()
    document = json.loads(args.evidence.read_text(encoding='utf-8'))
    finding = document['findings'][args.finding]
    if 'minimal_input' in finding:
        from ai_tests.fuzzing import observe
        report = observe(finding['minimal_input'], lambda data: weighted_boxes_fusion(**data))
        observed = finding['issue'] in report['violations']
        print(json.dumps(json_safe(dict(classification=finding['classification'],
                                        expected_issue=finding['issue'], reproduced=observed,
                                        report=report)), ensure_ascii=False, indent=2))
        # Replay success means reproducing an existing failure, not passing its property.
        return 0 if observed else 1
    left = weighted_boxes_fusion(**finding['input'])
    right = weighted_boxes_fusion(**finding['permuted_input'])
    observed = not same_output(left, right)
    print(json.dumps(json_safe(dict(classification=finding['classification'],
                                    expected_order_sensitivity_reproduced=observed,
                                    output=left, permuted_output=right)), ensure_ascii=False, indent=2))
    return 0 if observed else 1


if __name__ == '__main__':
    raise SystemExit(main())
