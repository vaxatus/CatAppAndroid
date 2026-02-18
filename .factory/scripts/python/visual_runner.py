"""
Visual regression runner — manages baselines, runs comparisons, generates diff reports.
Wraps Playwright screenshots, BackstopJS, and Maestro screenshot capture.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

from detect_platform import detect_platform


BASELINES_DIR = ".visual-baselines"


def run_cmd(cmd: list[str] | str, cwd: str, timeout: int = 300, shell: bool = False) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd}"


def setup_playwright_visual(root: str) -> dict:
    """Set up Playwright for visual regression testing."""
    result = {"action": "setup", "tool": "playwright", "files_created": [], "error": None}

    # Check if Playwright is installed
    code, stdout, _ = run_cmd(["npx", "playwright", "--version"], root)
    if code != 0:
        print("Installing Playwright...")
        code, stdout, stderr = run_cmd(["npm", "install", "-D", "@playwright/test"], root)
        if code != 0:
            result["error"] = f"Failed to install Playwright: {stderr[:300]}"
            return result
        run_cmd(["npx", "playwright", "install", "chromium"], root)

    # Create visual test directory
    visual_dir = Path(root) / "e2e" / "visual"
    visual_dir.mkdir(parents=True, exist_ok=True)

    # Create visual test config if no playwright config exists
    config_path = Path(root) / "playwright.config.ts"
    if not config_path.exists():
        config_path.write_text("""\
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
      caret: 'hide',
    },
  },
  projects: [
    { name: 'desktop-chrome', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
  ],
});
""")
        result["files_created"].append(str(config_path))

    return result


def setup_backstopjs(root: str) -> dict:
    """Set up BackstopJS for visual regression testing."""
    result = {"action": "setup", "tool": "backstopjs", "files_created": [], "error": None}

    code, _, stderr = run_cmd(["npx", "backstop", "--version"], root)
    if code != 0:
        print("Installing BackstopJS...")
        code, _, stderr = run_cmd(["npm", "install", "-D", "backstopjs"], root)
        if code != 0:
            result["error"] = f"Failed to install BackstopJS: {stderr[:300]}"
            return result

    config_path = Path(root) / "backstop.json"
    if not config_path.exists():
        config = {
            "id": "visual-regression",
            "viewports": [
                {"label": "desktop", "width": 1280, "height": 800},
                {"label": "tablet", "width": 768, "height": 1024},
                {"label": "mobile", "width": 375, "height": 812},
            ],
            "scenarios": [
                {
                    "label": "Homepage",
                    "url": "http://localhost:3000/",
                    "selectors": ["document"],
                    "misMatchThreshold": 0.1,
                    "delay": 2000,
                }
            ],
            "engine": "playwright",
            "engineOptions": {"browser": "chromium"},
            "paths": {
                "bitmaps_reference": "backstop_data/bitmaps_reference",
                "bitmaps_test": "backstop_data/bitmaps_test",
                "html_report": "backstop_data/html_report",
            },
            "report": ["browser"],
            "debug": False,
        }
        config_path.write_text(json.dumps(config, indent=2))
        result["files_created"].append(str(config_path))

    return result


def setup_maestro_visual(root: str) -> dict:
    """Set up Maestro screenshot directory."""
    result = {"action": "setup", "tool": "maestro", "files_created": [], "error": None}

    code, _, _ = run_cmd(["maestro", "--version"], root)
    if code != 0:
        result["error"] = "Maestro not installed. Run: curl -fsSL https://get.maestro.mobile.dev | bash"
        return result

    maestro_dir = Path(root) / ".maestro"
    maestro_dir.mkdir(exist_ok=True)
    screenshots_dir = maestro_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    result["files_created"].append(str(screenshots_dir))
    return result


def capture_playwright_baselines(root: str) -> dict:
    """Run Playwright tests with --update-snapshots to capture baselines."""
    result = {"action": "capture", "tool": "playwright", "screenshots": 0, "error": None}

    code, stdout, stderr = run_cmd(
        ["npx", "playwright", "test", "--update-snapshots"],
        root,
        timeout=300,
    )

    if code != 0:
        result["error"] = f"Playwright capture failed: {stderr[:500]}"
    else:
        # Count snapshot files created
        for snap_dir in Path(root).rglob("*-snapshots"):
            result["screenshots"] += len(list(snap_dir.glob("*.png")))

    result["stdout"] = stdout[:1000]
    return result


def run_backstopjs_reference(root: str) -> dict:
    """Run BackstopJS reference capture."""
    result = {"action": "capture", "tool": "backstopjs", "screenshots": 0, "error": None}

    code, stdout, stderr = run_cmd(["npx", "backstop", "reference"], root, timeout=300)

    if code != 0:
        result["error"] = f"BackstopJS reference failed: {stderr[:500]}"
    else:
        ref_dir = Path(root) / "backstop_data" / "bitmaps_reference"
        if ref_dir.exists():
            result["screenshots"] = len(list(ref_dir.rglob("*.png")))

    result["stdout"] = stdout[:1000]
    return result


def compare_backstopjs(root: str) -> dict:
    """Run BackstopJS comparison test."""
    result = {"action": "compare", "tool": "backstopjs", "passed": False, "report_path": None, "error": None}

    code, stdout, stderr = run_cmd(["npx", "backstop", "test"], root, timeout=300)

    report_path = Path(root) / "backstop_data" / "html_report" / "index.html"
    if report_path.exists():
        result["report_path"] = str(report_path)

    result["passed"] = code == 0
    if code != 0:
        result["error"] = "Visual differences detected. Check the report."

    result["stdout"] = stdout[:1000]
    return result


def compare_playwright(root: str) -> dict:
    """Run Playwright visual comparison."""
    result = {"action": "compare", "tool": "playwright", "passed": False, "report_path": None, "error": None}

    code, stdout, stderr = run_cmd(
        ["npx", "playwright", "test", "--grep", "@visual"],
        root,
        timeout=300,
    )

    result["passed"] = code == 0
    report_path = Path(root) / "playwright-report" / "index.html"
    if report_path.exists():
        result["report_path"] = str(report_path)

    if code != 0:
        result["error"] = "Visual differences detected or tests failed."

    result["stdout"] = stdout[:1000]
    return result


def run_visual(project_root: str, action: str) -> dict:
    detection = detect_platform(project_root)
    platforms = detection.get("platforms", [])
    tools = detection.get("testing_tools", [])

    primary = platforms[0] if platforms else "unknown"

    if action == "setup":
        if primary in ("web", "react-native"):
            result = setup_playwright_visual(project_root)
            backstop_result = setup_backstopjs(project_root)
            result["backstop"] = backstop_result
            return result
        elif primary in ("android", "ios"):
            return setup_maestro_visual(project_root)
        else:
            return {"error": f"Visual regression setup not implemented for: {primary}"}

    elif action == "capture":
        if "backstopjs" in tools:
            return run_backstopjs_reference(project_root)
        elif "playwright" in tools or primary == "web":
            return capture_playwright_baselines(project_root)
        else:
            return {"error": "No visual regression tool detected. Run setup first."}

    elif action == "compare":
        if "backstopjs" in tools:
            return compare_backstopjs(project_root)
        elif "playwright" in tools or primary == "web":
            return compare_playwright(project_root)
        else:
            return {"error": "No visual regression tool detected. Run setup first."}

    elif action == "update":
        if "backstopjs" in tools:
            code, stdout, stderr = run_cmd(["npx", "backstop", "approve"], project_root)
            return {"action": "update", "tool": "backstopjs", "success": code == 0}
        elif "playwright" in tools or primary == "web":
            return capture_playwright_baselines(project_root)
        else:
            return {"error": "No visual regression tool detected."}

    else:
        return {"error": f"Unknown action: {action}. Use: setup, capture, compare, update"}


def print_visual_report(result: dict):
    if "error" in result and result.get("action") is None:
        print(f"ERROR: {result['error']}")
        return

    print("=" * 60)
    print(f"VISUAL REGRESSION — {result.get('action', '').upper()}")
    print("=" * 60)
    print(f"Tool: {result.get('tool', 'unknown')}")

    if result.get("action") == "setup":
        files = result.get("files_created", [])
        if files:
            print("Files created:")
            for f in files:
                print(f"  + {f}")
        if result.get("backstop"):
            bs = result["backstop"]
            for f in bs.get("files_created", []):
                print(f"  + {f}")
    elif result.get("action") == "capture":
        print(f"Screenshots captured: {result.get('screenshots', 0)}")
    elif result.get("action") == "compare":
        status = "PASSED" if result.get("passed") else "FAILED — diffs detected"
        print(f"Result: {status}")
        if result.get("report_path"):
            print(f"Report: {result['report_path']}")

    if result.get("error"):
        print(f"Error: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 visual_runner.py <setup|capture|compare|update> [project_root]")
        sys.exit(1)
    action = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    result = run_visual(project, action)
    print_visual_report(result)
