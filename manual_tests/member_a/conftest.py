"""Record real WBF calls and pytest outcomes without changing the tested code."""
import contextlib
import hashlib
import io
import json
import platform
import subprocess
import traceback
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from ensemble_boxes import weighted_boxes_fusion

ROOT = Path(__file__).resolve().parents[2]


def pytest_addoption(parser):
    parser.addoption("--member-a-report", help="Write this run's member A evidence JSON")


def safe_json(value):
    if isinstance(value, np.ndarray):
        return safe_json(value.tolist())
    if isinstance(value, (list, tuple)):
        return [safe_json(v) for v in value]
    if isinstance(value, dict):
        return {k: safe_json(v) for k, v in value.items()}
    if isinstance(value, float) and not np.isfinite(value):
        return str(value)
    return value


def pytest_configure(config):
    config.member_a_records = []


@pytest.fixture
def probe(request):
    request.node.wbf_calls = []

    def invoke(params, scenario="spreadsheet_input"):
        stdout, stderr = io.StringIO(), io.StringIO()
        result, error, trace = None, None, None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    result = weighted_boxes_fusion(**params)
                except (Exception, SystemExit) as exc:
                    error = exc
                    trace = traceback.format_exc()
        record = {
            "scenario": scenario, "input": params,
            "output": None if result is None else dict(zip(("boxes", "scores", "labels"), result)),
            "shapes": None if result is None else [list(a.shape) for a in result],
            "exception": None if error is None else {
                "type": type(error).__name__, "message": str(error),
                "exit_code": getattr(error, "code", None), "traceback": trace},
            "warnings": [{"category": w.category.__name__, "message": str(w.message)} for w in caught],
            "stdout": stdout.getvalue(), "stderr": stderr.getvalue(),
        }
        request.node.wbf_calls.append(safe_json(record))
        return result, error, record
    return invoke


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" or report.failed:
        item.config.member_a_records.append({
            "case_id": item.name.split("__")[0].replace("test_", "WBF-UT-"),
            "nodeid": item.nodeid, "phase": report.when,
            "status": "OK" if report.passed else "NG" if report.failed else "NT",
            "duration_seconds": report.duration,
            "calls": getattr(item, "wbf_calls", []),
            "failure": report.longreprtext if report.failed else None,
        })


def pytest_sessionfinish(session, exitstatus):
    # This nested conftest can load after command-line parsing when the parent
    # manual_tests directory is selected; optional reporting must stay optional.
    target = session.config.getoption("--member-a-report", default=None)
    if not target:
        return
    source = ROOT / "ensemble_boxes/ensemble_boxes_wbf.py"
    frozen = subprocess.check_output(["git", "show", "reproduction-success:ensemble_boxes/ensemble_boxes_wbf.py"], cwd=ROOT)
    # Git can convert LF to CRLF on Windows; compare normalized source text as well.
    normalized = lambda b: b.replace(b"\r\n", b"\n")
    data = {
        "executed_at": datetime.now().astimezone().isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "numpy": np.__version__, "pytest": pytest.__version__,
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_path": "ensemble_boxes/ensemble_boxes_wbf.py",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "matches_reproduction_success": normalized(source.read_bytes()) == normalized(frozen),
        "pytest_exit_code": int(exitstatus), "results": session.config.member_a_records,
    }
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
