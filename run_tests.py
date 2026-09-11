"""Run all 30 module-1 cases and save genuine results; failures stay failures."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def case_number(node):
    name = node.get("name", "")
    patterns = [(name, r"^test_(\d{3})__"), (name, r"\[WBF-(\d{2})\]"),
                (node.get("classname", ""), r"test_wbf_(\d{2})(?:$|\.)")]
    for value, pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return int(match.group(1))
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New result directory; existing directories are not overwritten")
    args = parser.parse_args()
    output = args.output or ROOT / "test_results" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    junit = output / "junit.xml"
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    # A user's pytest addopts can hide cases or stop at the first failure.
    env.pop("PYTEST_ADDOPTS", None)
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "manual_tests", "-v", "--tb=short", "-rA",
               "-o", "addopts=", "-o", "junit_logging=all", "-o", "junit_log_passing_tests=true",
               f"--junitxml={junit}"]
    versions = {}
    for name in ("numpy", "numba", "llvmlite", "pandas", "pytest"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "NOT INSTALLED"
    source_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((ROOT / "ensemble_boxes").glob("*.py"))}
    started = datetime.now().astimezone().isoformat()
    with (output / "pytest.log").open("w", encoding="utf-8") as log:
        log.write("Command: " + subprocess.list2cmdline(command) + "\n\n")
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   encoding="utf-8", errors="replace")
        for line in process.stdout:
            print(line, end="")
            log.write(line)
        process.wait()
        log.write(f"\nPytest exit code: {process.returncode}\n")
    instances = []
    infrastructure_errors = []
    if junit.exists():
        try:
            for node in ET.parse(junit).iter("testcase"):
                error, failure, skipped = node.find("error"), node.find("failure"), node.find("skipped")
                status = "ERROR" if error is not None else "FAIL" if failure is not None else "SKIP" if skipped is not None else "PASS"
                number = case_number(node)
                instances.append({"case_id": f"WBF-UT-{number:03d}" if number is not None else None,
                                  "test": node.get("classname", "") + "::" + node.get("name", ""),
                                  "status": status, "duration_seconds": node.get("time"),
                                  "failure": (error.text if error is not None else failure.text if failure is not None else None)})
        except ET.ParseError as exc:
            infrastructure_errors.append(f"Invalid JUnit report: {exc}")
    else:
        infrastructure_errors.append("JUnit report missing; inspect pytest.log for dependency/collection errors.")
    groups = {}
    for item in instances:
        groups.setdefault(item["case_id"], []).append(item["status"])
    expected = {f"WBF-UT-{i:03d}" for i in range(1, 31)}
    missing = sorted(expected - groups.keys())
    unknown = [i["test"] for i in instances if i["case_id"] not in expected]
    if missing or unknown:
        infrastructure_errors.append(f"Case coverage mismatch; missing={missing}; unknown={unknown}")
    if any(i["status"] in ("ERROR", "SKIP") for i in instances):
        infrastructure_errors.append("Some tests errored or were skipped; not all 30 cases completed normally.")
    cases = [{"case_id": key, "status": "FAIL" if "FAIL" in values else "ERROR" if "ERROR" in values else "SKIP" if "SKIP" in values else "PASS",
              "instances": len(values)} for key, values in sorted(groups.items(), key=lambda pair: pair[0] or "") if key is not None]
    code = process.returncode
    if infrastructure_errors and code in (0, 1):
        code = 2
    report = {"started_at": started, "finished_at": datetime.now().astimezone().isoformat(),
              "python": platform.python_version(), "platform": platform.platform(), "dependencies": versions,
              "source_sha256": source_hashes, "pytest_exit_code": process.returncode, "runner_exit_code": code,
              "case_counts": dict(Counter(c["status"] for c in cases)),
              "instance_counts": dict(Counter(i["status"] for i in instances)),
              "cases": cases, "instances": instances, "infrastructure_errors": infrastructure_errors}
    (output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# WBF 模块1统一运行结果", "", f"执行时间：{started}",
             f"Python {report['python']}；依赖：{versions}", "",
             f"用例编号：{len(cases)}/30；实例：{len(instances)}。",
             f"按用例统计：{report['case_counts']}；按实例统计：{report['instance_counts']}。",
             f"pytest退出码：{process.returncode}；运行入口退出码：{code}。", "",
             "FAIL为真实断言失败，不代表脚本未执行。ERROR、缺少用例或依赖错误需先处理，不能当作已知缺陷。",
             "详细错误和捕获输出见 pytest.log、junit.xml、summary.json。", "",
             "| 用例 | 结果 | 实例数 |", "| --- | --- | --- |"]
    lines += [f"| {c['case_id']} | {c['status']} | {c['instances']} |" for c in cases]
    if infrastructure_errors:
        lines += ["", "## 运行异常", "", *infrastructure_errors]
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nResults: {output}\nCases: {len(cases)}/30 {report['case_counts']}\nExit code: {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
