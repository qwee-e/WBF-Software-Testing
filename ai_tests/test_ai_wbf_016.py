import copy
import json
import os
from pathlib import Path
import random

from ai_tests.fuzzing import (FUZZ_SEEDS, MUTATIONS, classify, extreme_weights, fresh_input,
                              minimize, mutate, observe, valid_input)
from ai_tests.support import MODES, digest, json_safe


def test_structured_fuzz(audit):
    budget = int(os.environ.get('AI_FUZZ_CANDIDATES', '3000'))
    assert budget >= 100 and budget % 50 == 0, 'Budget must be >=100 and divisible by 50'
    per_seed = budget // len(FUZZ_SEEDS)
    witnesses = {}
    trace = []
    failures = []
    audit.details.update(seeds=list(FUZZ_SEEDS), candidate_budget=budget,
                         normal_domain='positive scores [1e-8,1], weights [1e-6,1e6], labels 0..9, 1..6 models, <=20 boxes/model',
                         extreme_domain='10% candidates: weights 1e-100 / 1e200; exploratory only',
                         profile='formal' if budget >= 3000 else 'development',
                         score_upper_tolerance=1e-6)
    for seed in FUZZ_SEEDS:
        rng = random.Random(seed)
        exploratory_indices = set(random.Random(seed + 1000).sample(range(per_seed), per_seed // 10))
        corpus = [fresh_input(rng) for _ in range(8)]
        for index in range(per_seed):
            operation = MUTATIONS[index % len(MUTATIONS)]
            base = fresh_input(rng) if rng.random() < .5 else copy.deepcopy(rng.choice(corpus))
            data = mutate(base, rng, operation)
            data['conf_type'] = MODES[index % 4]
            data['allows_overflow'] = bool((index // 4) % 2)
            bucket = 'exploratory' if index in exploratory_indices else 'main'
            if bucket == 'exploratory':
                data = extreme_weights(data, rng)
            audit.counts['candidates'] += 1
            audit.counts[f'{bucket}_candidates'] += 1
            audit.counts[f'mutation:{operation}'] += 1
            if not valid_input(data, bucket):
                audit.counts['discarded'] += 1
                trace.append(dict(seed=seed, index=index, bucket=bucket, mutation=operation,
                                  input_sha256=digest(data), discarded=True))
                continue
            audit.counts['accepted'] += 1
            audit.counts[f'{bucket}_accepted'] += 1
            audit.counts[f'seed:{seed}:accepted'] += 1
            audit.source(data)
            report = observe(data, audit.call)
            audit.counts['candidate_calls'] += 1
            if report['warnings']:
                audit.counts[f'{bucket}_warning_inputs'] += 1
            if report['violations']:
                audit.counts[f'{bucket}_violating_inputs'] += 1
                failures.append(dict(seed=seed, candidate_index=index, mutation=operation,
                                     bucket=bucket, input=data, report=report,
                                     classifications=[classify(bucket, issue, data) for issue in report['violations']]))
            for issue in report['violations']:
                audit.counts[f'{bucket}:{issue}'] += 1
                key = (bucket, issue, data['conf_type'], data['allows_overflow'])
                witnesses.setdefault(key, dict(input=data, report=report, seed=seed, candidate_index=index,
                                               mutation=operation, bucket=bucket, issue=issue,
                                               classification=classify(bucket, issue, data)))
            trace.append(dict(seed=seed, index=index, bucket=bucket, mutation=operation,
                              input_sha256=digest(data), violations=report['violations']))
            if len(audit.samples) < 3:
                audit.samples.append(dict(input=data, report=report, seed=seed, candidate_index=index, bucket=bucket))
            if bucket == 'main':
                # Bounded seed pool retains valid generated structures, including failures.
                if report['violations'] or rng.random() < .1:
                    corpus.append(copy.deepcopy(data))
                    corpus = corpus[-32:]
    directory = Path(os.environ.get('AI_RESULTS_DIR', 'ai_test_results')) / audit.case
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'search_trace.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in trace), encoding='utf-8')
    (directory / 'failure_inputs.jsonl').write_text(
        ''.join(json.dumps(json_safe(row), allow_nan=False) + '\n' for row in failures), encoding='utf-8')
    for (bucket, issue, mode, overflow), witness in witnesses.items():
        def evaluate(candidate):
            audit.counts['shrink_calls'] += 1
            return observe(candidate, audit.call)

        minimal, attempts = minimize(witness['input'], bucket, issue, evaluate)
        audit.counts['shrink_attempts'] += attempts
        replays = [observe(minimal, audit.call) for _ in range(2)]
        audit.counts['replay_calls'] += 2
        assert all(issue in replay['violations'] for replay in replays), 'Minimized failure did not replay'
        witness.update(minimal_input=minimal, minimal_report=replays[0],
                       replay_confirmations=2,
                       retained_boxes=sum(map(len, minimal['boxes_list'])),
                       retained_models=len(minimal['weights']),
                       minimality='1-minimal under single-box or whole-model deletion; numerical values not minimized')
        audit.findings.append(witness)
    audit.details['witness_groups'] = len(witnesses)
    audit.details['classification_note'] = 'Do not count mode variants, known failures or exploratory risks as new confirmed bugs.'
    assert audit.counts['accepted'] >= .99 * budget, 'Generator rejected too many candidates'
    assert audit.counts['main_accepted'] >= .9 * budget, 'Insufficient main-domain coverage'
    print(json.dumps(json_safe(dict(counts=audit.counts, witness_groups=len(witnesses))), ensure_ascii=False))
    # Report real failures, including known bugs, after search/shrink/evidence collection.
    assert not audit.counts['main_violating_inputs'], (
        f"{audit.counts['main_violating_inputs']} main-domain inputs violated properties; "
        'see evidence.json for classification, minimal inputs and replays')
