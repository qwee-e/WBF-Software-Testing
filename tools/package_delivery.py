"""Build a standalone source ZIP, excluding environments and Git history."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verification", type=Path, required=True, help="Successful complete run's output directory (may contain assertion failures)")
    args = parser.parse_args()
    verification = args.verification.resolve()
    results = json.loads((verification / "summary.json").read_text(encoding="utf-8"))
    if results["infrastructure_errors"] or len(results["cases"]) != 30:
        raise SystemExit("Cannot package an incomplete run as complete evidence")
    for relative, digest in results["source_sha256"].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"Source changed after validation: {relative}")
    files = {}
    for name in ("run_tests.py", "run_tests.bat", "requirements-test.txt", "LICENSE", "manual_tests/README.md"):
        files[name] = (ROOT / name).read_bytes()
    guide = (ROOT / "docs/自动化测试工程_README.md").read_bytes()
    files["README.md"] = guide
    files["docs/自动化测试工程_README.md"] = guide
    for directory in ("ensemble_boxes", "tests"):
        for path in sorted((ROOT / directory).rglob("*.py")):
            files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in sorted((ROOT / "manual_tests").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if (path.name.startswith("test_") and path.suffix == ".py") or path.name == "conftest.py" or path.suffix in (".json", ".log") or (path.parent == ROOT / "manual_tests" and path.name.startswith("WBF-") and path.suffix == ".md"):
            files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in sorted((ROOT / "test_data").rglob("*.json")):
        files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in sorted((ROOT / "defects").glob("*/*.md")):
        files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for name in ("pytest.log", "junit.xml", "summary.json", "summary.md"):
        files[f"verification/{name}"] = (verification / name).read_bytes()
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())}
    files["MANIFEST.json"] = (json.dumps({"sha256": hashes}, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    destination = ROOT / "deliverables/WBF_module1_自动化测试工程.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            archive.writestr("WBF-module1-tests/" + name, content)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        for name, digest in hashes.items():
            assert hashlib.sha256(archive.read("WBF-module1-tests/" + name)).hexdigest() == digest
    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(f"{checksum}  {destination.name}\n", encoding="utf-8")
    print(f"Created {destination}\nFiles: {len(files)}\nSHA256: {checksum}")


if __name__ == "__main__":
    main()
