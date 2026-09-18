"""Run selected AI cases and save actual execution evidence (exit status preserved)."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', nargs='+', help='Case numbers, e.g. 001 002; default all implemented cases')
    parser.add_argument('--output', default='ai_test_results', help='Result directory, relative to project root')
    args = parser.parse_args()
    paths = sorted((ROOT / 'ai_tests').glob('test_ai_wbf_*.py'))
    requested = {n.removeprefix('AI-WBF-').zfill(3) for n in args.case} if args.case else None
    if requested:
        paths = [p for p in paths if p.stem.rsplit('_', 1)[-1] in requested]
        found = {p.stem.rsplit('_', 1)[-1] for p in paths}
        if found != requested:
            parser.error(f'Cases not implemented: {sorted(requested - found)}')
    if not paths:
        parser.error('No AI test files found')
    output = (ROOT / args.output).resolve()
    env = dict(os.environ, AI_RESULTS_DIR=str(output), PYTHONUTF8='1')
    source = ROOT / 'ensemble_boxes/ensemble_boxes_wbf.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    overall = 0
    for path in paths:
        case = 'AI-WBF-' + path.stem.rsplit('_', 1)[-1]
        target = output / case
        target.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, '-X', 'utf8', '-m', 'pytest', str(path.relative_to(ROOT)),
                   '-q', '-ra', '--tb=short', f'--junitxml={target / "pytest.xml"}']
        started = datetime.now(timezone.utc).isoformat()
        tick = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
        log = result.stdout + result.stderr
        (target / 'pytest.log').write_text(log, encoding='utf-8')
        print(log, end='')
        tests = ET.parse(target / 'pytest.xml').getroot().findall('.//testcase') if (target / 'pytest.xml').exists() else []
        metadata = dict(case=case, started_utc=started, elapsed_seconds=round(time.monotonic() - tick, 3),
                        command=command, exit_code=result.returncode,
                        pytest=dict(collected=len(tests), failed=sum(t.find('failure') is not None for t in tests),
                                    errors=sum(t.find('error') is not None for t in tests)),
                        python=platform.python_version(), platform=platform.platform(),
                        packages={p: importlib.metadata.version(p) for p in ('numpy', 'numba', 'pytest', 'hypothesis')},
                        execution_options={'AI_FUZZ_CANDIDATES': env.get('AI_FUZZ_CANDIDATES', '3000')},
                        test_code_sha256={str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in sorted((ROOT / 'ai_tests').glob('*.py'))},
                        source_sha256=before,
                        reference_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
        (target / 'run.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        evidence_path = target / 'evidence.json'
        counts = json.loads(evidence_path.read_text(encoding='utf-8'))['counts'] if evidence_path.exists() else {}
        summary = f'# {case} 执行记录\n\n'
        summary += f'- 状态：{"PASS" if result.returncode == 0 else "FAIL / 需阅读原始日志"}\n'
        summary += f'- UTC 开始时间：{started}\n- pytest 退出码：{result.returncode}\n'
        summary += f'- 实际计数：`{json.dumps(counts, ensure_ascii=False)}`\n'
        summary += '- 原始输出：`pytest.log`；机器结果：`pytest.xml`；环境与命令：`run.json`；输入及性质比较：`evidence.json`。\n'
        summary += '- 生成输入次数不等于 pytest 用例条数；调用计数包含基准、变换、重放及缩减（如有）。\n'
        (target / 'summary.md').write_text(summary, encoding='utf-8')
        overall = overall or result.returncode
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before, 'Tested source changed'
    return overall


if __name__ == '__main__':
    raise SystemExit(main())
