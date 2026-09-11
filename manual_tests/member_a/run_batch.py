"""Execute only the requested cases and persist pytest's actual output/exit code."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", help="Unique batch number, e.g. 01")
    parser.add_argument("ids", nargs="+", type=int)
    args = parser.parse_args()
    destination = ROOT / "manual_tests/member_a/results" / f"batch_{args.batch}"
    destination.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-m", "pytest", "manual_tests/member_a/test_wbf_member_a.py",
               "-v", "--tb=short", "-k", " or ".join(f"test_{i:03d}__" for i in args.ids),
               f"--member-a-report={destination / 'results.json'}"]
    run = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         encoding="utf-8", errors="replace")
    (destination / "pytest.log").write_text(
        "Command: " + subprocess.list2cmdline(command) + "\n\n" + run.stdout +
        f"\nExit code: {run.returncode}\n", encoding="utf-8")
    print(run.stdout)
    report = destination / "results.json"
    if not report.exists():
        raise RuntimeError("pytest did not produce evidence; inspect pytest.log")
    data = json.loads(report.read_text(encoding="utf-8"))
    expected = {f"WBF-UT-{i:03d}" for i in args.ids}
    actual = [r["case_id"] for r in data["results"]]
    if set(actual) != expected or len(actual) != len(expected):
        raise RuntimeError(f"Unexpected selected cases: {actual}; expected {expected}")
    if not data["matches_reproduction_success"]:
        raise RuntimeError("Tested WBF source differs from the frozen baseline")
    sys.exit(run.returncode)


if __name__ == "__main__":
    main()
