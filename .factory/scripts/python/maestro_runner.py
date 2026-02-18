"""
Maestro flow runner — generates, runs, and manages Maestro YAML test flows.
Handles Android and iOS via Maestro CLI.
"""

import os
import sys
import subprocess
from pathlib import Path

from detect_platform import detect_platform


def run_cmd(cmd: list[str], cwd: str, timeout: int = 300) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_maestro() -> bool:
    code, _, _ = run_cmd(["maestro", "--version"], os.getcwd())
    return code == 0


def check_devices() -> dict:
    result = {"android": False, "ios": False, "android_devices": [], "ios_devices": []}

    code, stdout, _ = run_cmd(["adb", "devices"], os.getcwd())
    if code == 0:
        lines = stdout.strip().split("\n")[1:]  # skip header
        devices = [l.split("\t")[0] for l in lines if "\tdevice" in l]
        result["android"] = len(devices) > 0
        result["android_devices"] = devices

    code, stdout, _ = run_cmd(["xcrun", "simctl", "list", "devices", "booted", "--json"], os.getcwd())
    if code == 0:
        import json
        try:
            data = json.loads(stdout)
            for runtime, devs in data.get("devices", {}).items():
                for dev in devs:
                    if dev.get("state") == "Booted":
                        result["ios"] = True
                        result["ios_devices"].append(dev.get("name", "unknown"))
        except (json.JSONDecodeError, KeyError):
            pass

    return result


def find_app_id(root: str) -> str | None:
    root_path = Path(root)

    # Android — search build.gradle.kts
    for gradle in root_path.rglob("build.gradle.kts"):
        content = gradle.read_text(errors="ignore")
        for line in content.split("\n"):
            if "applicationId" in line:
                # applicationId = "com.example.app"
                parts = line.split('"')
                if len(parts) >= 2:
                    return parts[1]

    # Android — search build.gradle
    for gradle in root_path.rglob("build.gradle"):
        content = gradle.read_text(errors="ignore")
        for line in content.split("\n"):
            if "applicationId" in line:
                parts = line.split("'") if "'" in line else line.split('"')
                if len(parts) >= 2:
                    return parts[1]

    # iOS — search pbxproj
    for pbx in root_path.rglob("project.pbxproj"):
        content = pbx.read_text(errors="ignore")
        for line in content.split("\n"):
            if "PRODUCT_BUNDLE_IDENTIFIER" in line:
                parts = line.split("=")
                if len(parts) >= 2:
                    return parts[1].strip().rstrip(";").strip().strip('"')

    return None


def init_maestro(root: str, app_id: str | None = None) -> dict:
    """Initialize .maestro directory with a smoke test template."""
    result = {"action": "init", "files_created": [], "error": None}

    maestro_dir = Path(root) / ".maestro"
    flows_dir = maestro_dir / "flows"
    for sub in ["auth", "navigation", "features", "smoke"]:
        (flows_dir / sub).mkdir(parents=True, exist_ok=True)

    screenshots_dir = maestro_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    if app_id is None:
        app_id = find_app_id(root) or "com.example.app"

    # Create config
    config_path = maestro_dir / "config.yaml"
    if not config_path.exists():
        config_path.write_text(f"""\
# Maestro configuration
# Docs: https://maestro.mobile.dev/
appId: {app_id}
""")
        result["files_created"].append(str(config_path))

    # Create smoke test template
    smoke_path = flows_dir / "smoke" / "critical-path.yaml"
    if not smoke_path.exists():
        smoke_path.write_text(f"""\
appId: {app_id}
tags:
  - smoke
  - critical
---
- launchApp:
    clearState: true

# TODO: Replace with your app's actual UI flow
- assertVisible: "Welcome"
- takeScreenshot: "01-launch"

# Example: login flow
# - tapOn:
#     id: "email_input"
# - inputText: "${{EMAIL}}"
# - tapOn:
#     id: "password_input"
# - inputText: "${{PASSWORD}}"
# - tapOn: "Sign In"
# - assertVisible: "Home"
# - takeScreenshot: "02-home"
""")
        result["files_created"].append(str(smoke_path))

    # Create login template
    login_path = flows_dir / "auth" / "login.yaml"
    if not login_path.exists():
        login_path.write_text(f"""\
appId: {app_id}
tags:
  - auth
---
- launchApp:
    clearState: true

# TODO: Update selectors to match your app
- assertVisible: "Sign In"

- tapOn:
    id: "email_input"
- inputText: "${{EMAIL}}"

- tapOn:
    id: "password_input"
- inputText: "${{PASSWORD}}"

- tapOn: "Sign In"
- assertVisible: "Home"
- takeScreenshot: "login-success"
""")
        result["files_created"].append(str(login_path))

    # Create .env template
    env_path = maestro_dir / ".env.example"
    if not env_path.exists():
        env_path.write_text("""\
# Test credentials (never commit real credentials)
EMAIL=test@example.com
PASSWORD=TestPassword123!
API_URL=https://staging.example.com
""")
        result["files_created"].append(str(env_path))

    return result


def run_flows(root: str, tag: str | None = None, flow_path: str | None = None) -> dict:
    """Run Maestro flows."""
    result = {"action": "run", "passed": False, "error": None, "output": ""}

    if not check_maestro():
        result["error"] = "Maestro not installed. Run: curl -fsSL https://get.maestro.mobile.dev | bash"
        return result

    devices = check_devices()
    if not devices["android"] and not devices["ios"]:
        result["error"] = "No connected devices or running emulators/simulators found."
        return result

    cmd = ["maestro", "test"]
    if tag:
        cmd.extend(["--include-tags", tag])

    if flow_path:
        cmd.append(flow_path)
    else:
        maestro_flows = os.path.join(root, ".maestro", "flows")
        if os.path.isdir(maestro_flows):
            cmd.append(maestro_flows)
        else:
            result["error"] = ".maestro/flows directory not found. Run init first."
            return result

    code, stdout, stderr = run_cmd(cmd, root, timeout=600)
    result["passed"] = code == 0
    result["output"] = stdout[:2000]
    if code != 0:
        result["error"] = f"Some flows failed. {stderr[:500]}"

    return result


def record_flow(root: str, flow_path: str) -> dict:
    """Record a Maestro flow with video."""
    result = {"action": "record", "video_path": None, "error": None}

    if not check_maestro():
        result["error"] = "Maestro not installed."
        return result

    code, stdout, stderr = run_cmd(
        ["maestro", "record", flow_path],
        root,
        timeout=600,
    )

    if code != 0:
        result["error"] = f"Recording failed: {stderr[:500]}"

    result["output"] = stdout[:1000]
    return result


def list_flows(root: str) -> dict:
    """List all Maestro flows in the project."""
    result = {"flows": [], "total": 0}

    maestro_dir = Path(root) / ".maestro" / "flows"
    if not maestro_dir.exists():
        return result

    for yaml_file in sorted(maestro_dir.rglob("*.yaml")):
        rel = yaml_file.relative_to(Path(root))
        tags = []
        content = yaml_file.read_text(errors="ignore")
        in_tags = False
        for line in content.split("\n"):
            if line.strip().startswith("tags:"):
                in_tags = True
                continue
            if in_tags and line.strip().startswith("- "):
                tags.append(line.strip()[2:])
            elif in_tags and not line.strip().startswith("-"):
                in_tags = False

        result["flows"].append({
            "path": str(rel),
            "name": yaml_file.stem,
            "tags": tags,
        })

    result["total"] = len(result["flows"])
    return result


def print_maestro_report(result: dict):
    print("=" * 60)
    print(f"MAESTRO — {result.get('action', 'unknown').upper()}")
    print("=" * 60)

    if result.get("action") == "init":
        if result.get("files_created"):
            print("Files created:")
            for f in result["files_created"]:
                print(f"  + {f}")
        print("\nNext: edit the YAML flows to match your app's UI, then run:")
        print("  python3 test-runner.py maestro run --tag smoke")

    elif result.get("action") == "run":
        status = "PASSED" if result.get("passed") else "FAILED"
        print(f"Result: {status}")
        if result.get("output"):
            print(result["output"][:500])

    if result.get("error"):
        print(f"\nError: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 maestro_runner.py <init|run|list|record> [options] [project_root]")
        print("  init [project_root]           — Initialize .maestro directory")
        print("  run [--tag TAG] [project_root] — Run flows")
        print("  list [project_root]            — List all flows")
        print("  record <flow.yaml>             — Record a flow with video")
        sys.exit(0)

    action = sys.argv[1]

    if action == "init":
        project = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        result = init_maestro(project)
        print_maestro_report(result)
    elif action == "run":
        tag = None
        project = os.getcwd()
        args = sys.argv[2:]
        if "--tag" in args:
            idx = args.index("--tag")
            tag = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        if args:
            project = args[0]
        result = run_flows(project, tag=tag)
        print_maestro_report(result)
    elif action == "list":
        project = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        result = list_flows(project)
        print(f"Found {result['total']} Maestro flow(s):")
        for f in result["flows"]:
            tags = f" [{', '.join(f['tags'])}]" if f["tags"] else ""
            print(f"  {f['path']}{tags}")
    elif action == "record":
        if len(sys.argv) < 3:
            print("Usage: python3 maestro_runner.py record <flow.yaml>")
            sys.exit(1)
        result = record_flow(os.getcwd(), sys.argv[2])
        print_maestro_report(result)
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
