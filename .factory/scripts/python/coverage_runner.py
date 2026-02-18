"""
Runs coverage tools for the detected platform and parses the results.
Wraps JaCoCo, Istanbul/c8, xcov, pytest-cov, go cover.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path

from detect_platform import detect_platform


def run_cmd(cmd: list[str], cwd: str, timeout: int = 300) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def run_web_coverage(root: str, tools: list[str]) -> dict:
    result = {"tool": None, "overall": None, "details": [], "report_path": None, "error": None}

    if "vitest" in tools:
        result["tool"] = "vitest"
        code, stdout, stderr = run_cmd(["npx", "vitest", "run", "--coverage", "--reporter=json"], root)
    elif "jest" in tools:
        result["tool"] = "jest"
        code, stdout, stderr = run_cmd(["npx", "jest", "--coverage", "--coverageReporters=json-summary"], root)
    else:
        result["tool"] = "vitest"
        code, stdout, stderr = run_cmd(["npx", "vitest", "run", "--coverage"], root)

    if code != 0:
        result["error"] = f"Coverage command failed (exit {code}): {stderr[:500]}"
        return result

    # Try to parse coverage summary
    summary_paths = [
        Path(root) / "coverage" / "coverage-summary.json",
        Path(root) / "coverage" / "coverage-final.json",
    ]
    for sp in summary_paths:
        if sp.exists():
            try:
                data = json.loads(sp.read_text())
                total = data.get("total", {})
                if total:
                    lines = total.get("lines", {})
                    result["overall"] = lines.get("pct", 0)
                    result["report_path"] = str(sp.parent / "lcov-report" / "index.html")
                    for filename, file_data in data.items():
                        if filename == "total":
                            continue
                        file_lines = file_data.get("lines", {})
                        result["details"].append({
                            "file": filename,
                            "lines": file_lines.get("pct", 0),
                            "branches": file_data.get("branches", {}).get("pct", 0),
                        })
                break
            except (json.JSONDecodeError, KeyError):
                pass

    if result["overall"] is None:
        # Parse from stdout as fallback
        pct_match = re.search(r"All files\s*\|\s*([\d.]+)", stdout)
        if pct_match:
            result["overall"] = float(pct_match.group(1))

    return result


def run_android_coverage(root: str) -> dict:
    result = {"tool": "jacoco", "overall": None, "details": [], "report_path": None, "error": None}

    gradlew = os.path.join(root, "gradlew")
    if not os.path.exists(gradlew):
        result["error"] = "gradlew not found in project root"
        return result

    code, stdout, stderr = run_cmd(
        ["./gradlew", "testDebugUnitTest", "jacocoTestReport"],
        root,
        timeout=600,
    )

    if code != 0:
        result["error"] = f"Gradle command failed (exit {code}): {stderr[:500]}"
        return result

    # Find JaCoCo report
    report_paths = list(Path(root).rglob("jacoco/test/html/index.html")) + \
                   list(Path(root).rglob("jacocoTestReport/html/index.html"))

    if report_paths:
        result["report_path"] = str(report_paths[0])

    # Parse XML report for percentages
    xml_reports = list(Path(root).rglob("jacoco*.xml"))
    for xml_path in xml_reports:
        content = xml_path.read_text(errors="ignore")
        # Simple regex parse for counters
        line_match = re.search(
            r'<counter type="LINE" missed="(\d+)" covered="(\d+)"',
            content,
        )
        if line_match:
            missed = int(line_match.group(1))
            covered = int(line_match.group(2))
            total = missed + covered
            result["overall"] = round((covered / total) * 100, 1) if total > 0 else 0
            break

    return result


def run_ios_coverage(root: str) -> dict:
    result = {"tool": "xcov", "overall": None, "details": [], "report_path": None, "error": None}

    # Find scheme name
    xcodeproj_dirs = list(Path(root).glob("*.xcodeproj"))
    if not xcodeproj_dirs:
        result["error"] = "No .xcodeproj found"
        return result

    scheme = xcodeproj_dirs[0].stem

    code, stdout, stderr = run_cmd([
        "xcodebuild", "test",
        "-scheme", scheme,
        "-destination", "platform=iOS Simulator,name=iPhone 16",
        "-enableCodeCoverage", "YES",
        "-resultBundlePath", os.path.join(root, "TestResults.xcresult"),
    ], root, timeout=600)

    if code != 0:
        result["error"] = f"xcodebuild failed (exit {code}): {stderr[:500]}"
        return result

    xcresult = os.path.join(root, "TestResults.xcresult")
    if os.path.exists(xcresult):
        result["report_path"] = xcresult
        code2, stdout2, _ = run_cmd([
            "xcrun", "xccov", "view", "--report", "--json", xcresult,
        ], root)
        if code2 == 0:
            try:
                data = json.loads(stdout2)
                result["overall"] = data.get("lineCoverage", 0) * 100
                for target in data.get("targets", []):
                    for f in target.get("files", []):
                        result["details"].append({
                            "file": f.get("name", ""),
                            "lines": round(f.get("lineCoverage", 0) * 100, 1),
                        })
            except (json.JSONDecodeError, KeyError):
                pass

    return result


def run_spring_coverage(root: str) -> dict:
    result = {"tool": "jacoco", "overall": None, "details": [], "report_path": None, "error": None}

    # Check Maven vs Gradle
    if os.path.exists(os.path.join(root, "pom.xml")):
        code, stdout, stderr = run_cmd(["mvn", "test", "jacoco:report"], root, timeout=600)
        report_glob = "target/site/jacoco/index.html"
    else:
        gradlew = os.path.join(root, "gradlew")
        if not os.path.exists(gradlew):
            result["error"] = "Neither pom.xml nor gradlew found"
            return result
        code, stdout, stderr = run_cmd(
            ["./gradlew", "test", "jacocoTestReport"], root, timeout=600
        )
        report_glob = "build/reports/jacoco/test/html/index.html"

    if code != 0:
        result["error"] = f"Build failed (exit {code}): {stderr[:500]}"
        return result

    reports = list(Path(root).rglob(report_glob.split("/")[-1]))
    if reports:
        result["report_path"] = str(reports[0])

    # Parse XML
    xml_reports = list(Path(root).rglob("jacoco*.xml"))
    for xml_path in xml_reports:
        content = xml_path.read_text(errors="ignore")
        line_match = re.search(
            r'<counter type="LINE" missed="(\d+)" covered="(\d+)"',
            content,
        )
        if line_match:
            missed = int(line_match.group(1))
            covered = int(line_match.group(2))
            total = missed + covered
            result["overall"] = round((covered / total) * 100, 1) if total > 0 else 0
            break

    return result


def run_python_coverage(root: str) -> dict:
    result = {"tool": "pytest-cov", "overall": None, "details": [], "report_path": None, "error": None}

    # Find the source directory
    src_candidates = ["src", "app", "lib"]
    src_dir = None
    for candidate in src_candidates:
        if os.path.isdir(os.path.join(root, candidate)):
            src_dir = candidate
            break

    cmd = ["python3", "-m", "pytest", "--cov", "--cov-report=json", "--cov-report=html"]
    if src_dir:
        cmd.extend([f"--cov={src_dir}"])

    code, stdout, stderr = run_cmd(cmd, root, timeout=300)

    if code != 0 and code != 1:  # pytest returns 1 for test failures
        result["error"] = f"pytest failed (exit {code}): {stderr[:500]}"
        return result

    cov_json = Path(root) / "coverage.json"
    if cov_json.exists():
        try:
            data = json.loads(cov_json.read_text())
            result["overall"] = data.get("totals", {}).get("percent_covered", 0)
            result["report_path"] = str(Path(root) / "htmlcov" / "index.html")
            for filename, file_data in data.get("files", {}).items():
                result["details"].append({
                    "file": filename,
                    "lines": file_data.get("summary", {}).get("percent_covered", 0),
                })
        except (json.JSONDecodeError, KeyError):
            pass

    return result


def run_coverage(project_root: str) -> dict:
    detection = detect_platform(project_root)
    platforms = detection.get("platforms", [])
    tools = detection.get("testing_tools", [])

    if not platforms:
        return {"error": "Could not detect project platform", "detection": detection}

    # Pick the primary platform
    primary = platforms[0]
    coverage_result = None

    if primary in ("web", "react-native"):
        coverage_result = run_web_coverage(project_root, tools)
    elif primary == "android":
        coverage_result = run_android_coverage(project_root)
    elif primary == "ios":
        coverage_result = run_ios_coverage(project_root)
    elif primary == "spring":
        coverage_result = run_spring_coverage(project_root)
    elif primary == "python":
        coverage_result = run_python_coverage(project_root)
    else:
        return {"error": f"Coverage not supported for platform: {primary}", "detection": detection}

    coverage_result["platform"] = primary
    coverage_result["detection"] = detection
    return coverage_result


def print_coverage_report(result: dict):
    if "error" in result and result.get("overall") is None:
        print(f"ERROR: {result['error']}")
        return

    print("=" * 60)
    print("COVERAGE REPORT")
    print("=" * 60)
    print(f"Platform: {result.get('platform', 'unknown')}")
    print(f"Tool: {result.get('tool', 'unknown')}")
    print(f"Overall coverage: {result.get('overall', 'N/A')}%")
    if result.get("report_path"):
        print(f"HTML report: {result['report_path']}")
    if result.get("error"):
        print(f"Warning: {result['error']}")
    print()

    details = result.get("details", [])
    if details:
        # Sort by coverage ascending (worst first)
        details.sort(key=lambda d: d.get("lines", 0))
        print("Files by coverage (lowest first):")
        for d in details[:20]:
            lines = d.get("lines", 0)
            marker = "!!" if lines < 50 else "  "
            print(f"  {marker} {lines:5.1f}%  {d['file']}")
        if len(details) > 20:
            print(f"  ... and {len(details) - 20} more files")
    print("=" * 60)


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = run_coverage(project)
    print_coverage_report(result)
