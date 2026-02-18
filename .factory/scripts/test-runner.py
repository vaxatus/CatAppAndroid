#!/usr/bin/env python3
"""
UI Test Runner CLI — unified entry point for all UI testing operations.

Usage:
  ./test-runner.py <command> [options] [project_path]

Commands:
  detect          Detect project platform and installed testing tools
  setup           Install and configure testing tools for the detected platform
  coverage        Run test coverage analysis
  generate        Generate E2E test boilerplate (Playwright or Maestro)
  run             Run E2E tests
  visual setup    Set up visual regression infrastructure
  visual capture  Capture baseline screenshots
  visual compare  Compare screenshots against baselines
  visual update   Accept current screenshots as new baselines
  maestro init    Initialize Maestro flow directory
  maestro run     Run Maestro flows
  maestro list    List all Maestro flows
  screenshot      Take a screenshot of a URL (Node.js/Playwright)
  diff            Compare two screenshot images (Node.js/pixelmatch)
  report          Show summary of all testing status

Options:
  --project, -p   Project root directory (default: current directory)
  --tag, -t       Filter by tag (for Maestro flows)
  --platform      Override detected platform (web|android|ios)
  --verbose, -v   Verbose output
"""

import os
import sys
import json
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent / "scripts"
PYTHON_SCRIPTS = SCRIPTS_DIR / "python"
NODE_SCRIPTS = SCRIPTS_DIR / "node"


def run_python_script(script: str, args: list[str], cwd: str | None = None) -> int:
    script_path = PYTHON_SCRIPTS / script
    cmd = [sys.executable, str(script_path)] + args
    return subprocess.call(cmd, cwd=cwd, env={**os.environ, "PYTHONPATH": str(PYTHON_SCRIPTS)})


def run_node_script(script: str, args: list[str], cwd: str | None = None) -> int:
    script_path = NODE_SCRIPTS / script
    # Check if node_modules exists
    node_modules = NODE_SCRIPTS / "node_modules"
    if not node_modules.exists():
        print("Installing Node.js dependencies...")
        subprocess.call(["npm", "install"], cwd=str(NODE_SCRIPTS))
    cmd = ["node", str(script_path)] + args
    return subprocess.call(cmd, cwd=cwd)


def ensure_node_deps():
    node_modules = NODE_SCRIPTS / "node_modules"
    if not node_modules.exists():
        print("Installing Node.js dependencies (first run)...")
        code = subprocess.call(["npm", "install"], cwd=str(NODE_SCRIPTS))
        if code != 0:
            print("ERROR: Failed to install Node.js dependencies.")
            print("Make sure Node.js and npm are installed.")
            sys.exit(1)


def cmd_detect(args: list[str]):
    project = args[0] if args else os.getcwd()
    run_python_script("detect_platform.py", [project])


def cmd_setup(args: list[str]):
    project = args[0] if args else os.getcwd()

    # Detect platform first
    sys.path.insert(0, str(PYTHON_SCRIPTS))
    from detect_platform import detect_platform
    result = detect_platform(project)
    platforms = result.get("platforms", [])

    if not platforms:
        print("ERROR: Could not detect project platform.")
        print("Make sure you're in a project directory with build files.")
        sys.exit(1)

    primary = platforms[0]
    print(f"Detected platform: {primary}")
    print(f"Frameworks: {', '.join(result.get('frameworks', []))}")
    print()

    # Install tools
    if primary in ("web", "react-native"):
        print("Setting up Playwright...")
        code = subprocess.call(["npm", "install", "-D", "@playwright/test"], cwd=project)
        if code == 0:
            subprocess.call(["npx", "playwright", "install", "chromium"], cwd=project)
            print("Playwright installed.")
        else:
            print("WARNING: Failed to install Playwright.")

    if primary in ("android", "ios", "react-native", "flutter"):
        print("Checking Maestro...")
        code = subprocess.call(["maestro", "--version"], capture_output=True)
        if code != 0:
            print("Maestro not found. Install with:")
            print("  curl -fsSL https://get.maestro.mobile.dev | bash")
        else:
            print("Maestro already installed.")

        # Initialize Maestro directory
        from maestro_runner import init_maestro
        init_result = init_maestro(project)
        if init_result.get("files_created"):
            print("Maestro directory initialized:")
            for f in init_result["files_created"]:
                print(f"  + {f}")

    # Set up visual regression
    print()
    print("Setting up visual regression...")
    from visual_runner import run_visual
    vis_result = run_visual(project, "setup")
    if vis_result.get("files_created"):
        for f in vis_result["files_created"]:
            print(f"  + {f}")

    print()
    print("Setup complete. Run './test-runner.py detect' to verify.")


def cmd_coverage(args: list[str]):
    project = args[0] if args else os.getcwd()
    run_python_script("coverage_runner.py", [project])


def cmd_generate(args: list[str]):
    project = args[0] if args else os.getcwd()

    sys.path.insert(0, str(PYTHON_SCRIPTS))
    from detect_platform import detect_platform
    result = detect_platform(project)
    platforms = result.get("platforms", [])
    primary = platforms[0] if platforms else "unknown"

    if primary in ("android", "ios", "react-native", "flutter"):
        from maestro_runner import init_maestro
        init_result = init_maestro(project)
        print("Generated Maestro flow templates:")
        for f in init_result.get("files_created", []):
            print(f"  + {f}")
        if not init_result.get("files_created"):
            print("  (flows already exist)")
        print()
        print("Next steps:")
        print("  1. Edit the YAML flows in .maestro/flows/ to match your app's UI")
        print("  2. Run: ./test-runner.py maestro run --tag smoke")
    elif primary == "web":
        print("For web projects, generate Playwright tests by using the droid:")
        print('  "Use the subagent web-e2e-generator to generate E2E tests for this project"')
        print()
        print("Or set up the visual regression infrastructure:")
        print("  ./test-runner.py visual setup")
    else:
        print(f"Test generation for platform '{primary}' — use the droid:")
        print('  "Use the subagent ui-test-master to generate tests for this project"')


def cmd_run(args: list[str]):
    project = args[0] if args else os.getcwd()

    sys.path.insert(0, str(PYTHON_SCRIPTS))
    from detect_platform import detect_platform
    result = detect_platform(project)
    platforms = result.get("platforms", [])
    tools = result.get("testing_tools", [])
    primary = platforms[0] if platforms else "unknown"

    ran_something = False

    if "playwright" in tools or primary == "web":
        print("Running Playwright tests...")
        code = subprocess.call(["npx", "playwright", "test"], cwd=project)
        ran_something = True
        if code == 0:
            print("Playwright tests PASSED")
        else:
            print("Playwright tests FAILED")
        print()

    if primary in ("android", "ios", "react-native", "flutter"):
        maestro_dir = Path(project) / ".maestro" / "flows"
        if maestro_dir.exists():
            print("Running Maestro flows...")
            code = subprocess.call(["maestro", "test", str(maestro_dir)], cwd=project)
            ran_something = True
            if code == 0:
                print("Maestro flows PASSED")
            else:
                print("Maestro flows FAILED")

    if not ran_something:
        print("No E2E tests found to run.")
        print("Run './test-runner.py setup' or './test-runner.py generate' first.")


def cmd_visual(args: list[str]):
    if not args:
        print("Usage: ./test-runner.py visual <setup|capture|compare|update> [project_path]")
        sys.exit(1)
    action = args[0]
    project = args[1] if len(args) > 1 else os.getcwd()
    run_python_script("visual_runner.py", [action, project])


def cmd_maestro(args: list[str]):
    if not args:
        print("Usage: ./test-runner.py maestro <init|run|list|record> [options]")
        sys.exit(1)
    run_python_script("maestro_runner.py", args)


def cmd_screenshot(args: list[str]):
    if not args:
        print("Usage: ./test-runner.py screenshot <url> [output.png] [--device=name] [--full-page]")
        sys.exit(1)
    ensure_node_deps()
    run_node_script("screenshot.js", args)


def cmd_diff(args: list[str]):
    if len(args) < 2:
        print("Usage: ./test-runner.py diff <baseline.png> <current.png> [diff.png] [--threshold=0.1]")
        sys.exit(1)
    ensure_node_deps()
    run_node_script("visual-diff.js", args)


def cmd_report(args: list[str]):
    project = args[0] if args else os.getcwd()
    print("=" * 60)
    print("UI TEST STATUS REPORT")
    print("=" * 60)
    print()

    # Detect platform
    sys.path.insert(0, str(PYTHON_SCRIPTS))
    from detect_platform import detect_platform
    result = detect_platform(project)

    print(f"Project: {project}")
    print(f"Platforms: {', '.join(result.get('platforms', ['none']))}")
    print(f"Frameworks: {', '.join(result.get('frameworks', ['none']))}")
    print(f"Testing tools: {', '.join(result.get('testing_tools', ['none']))}")
    print()

    # Count test files
    root = Path(project)

    playwright_tests = list(root.rglob("*.spec.ts")) + list(root.rglob("*.spec.js"))
    playwright_tests = [t for t in playwright_tests if "node_modules" not in str(t)]
    print(f"Playwright test files: {len(playwright_tests)}")

    maestro_flows = list((root / ".maestro").rglob("*.yaml")) if (root / ".maestro").exists() else []
    print(f"Maestro flow files: {len(maestro_flows)}")

    # Count visual baselines
    snapshot_dirs = list(root.rglob("*-snapshots"))
    snapshot_files = sum(len(list(d.glob("*.png"))) for d in snapshot_dirs)
    backstop_refs = list((root / "backstop_data" / "bitmaps_reference").rglob("*.png")) if (root / "backstop_data").exists() else []
    print(f"Visual baselines: {snapshot_files + len(backstop_refs)} screenshots")

    print()
    if result.get("missing_tools"):
        print("Missing tools:")
        for t in result["missing_tools"]:
            print(f"  - {t}")
    if result.get("recommendations"):
        print("Recommendations:")
        for r in result["recommendations"]:
            print(f"  - {r}")
    print("=" * 60)


def print_help():
    print(__doc__)


COMMANDS = {
    "detect": cmd_detect,
    "setup": cmd_setup,
    "coverage": cmd_coverage,
    "generate": cmd_generate,
    "run": cmd_run,
    "visual": cmd_visual,
    "maestro": cmd_maestro,
    "screenshot": cmd_screenshot,
    "diff": cmd_diff,
    "report": cmd_report,
    "help": lambda _: print_help(),
    "--help": lambda _: print_help(),
    "-h": lambda _: print_help(),
}


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command in COMMANDS:
        COMMANDS[command](args)
    else:
        print(f"Unknown command: {command}")
        print()
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
