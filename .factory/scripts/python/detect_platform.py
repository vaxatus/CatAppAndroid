"""
Detects the project technology stack by scanning for known build/config files.
Returns a structured result with platform, detected tools, and recommendations.
"""

import os
import json
from pathlib import Path


PLATFORM_SIGNALS = {
    "web": {
        "files": ["package.json"],
        "extra_signals": {
            "next.config.js": "Next.js",
            "next.config.ts": "Next.js",
            "next.config.mjs": "Next.js",
            "vite.config.ts": "Vite",
            "vite.config.js": "Vite",
            "angular.json": "Angular",
            "vue.config.js": "Vue",
            "nuxt.config.ts": "Nuxt",
            "svelte.config.js": "SvelteKit",
            "remix.config.js": "Remix",
            "astro.config.mjs": "Astro",
        },
    },
    "android": {
        "files": ["AndroidManifest.xml", "build.gradle", "build.gradle.kts"],
        "search_dirs": ["app/src/main", "src/main"],
    },
    "ios": {
        "extensions": [".xcodeproj", ".xcworkspace"],
        "files": ["Package.swift", "Podfile"],
    },
    "react-native": {
        "package_json_deps": ["react-native", "expo"],
    },
    "flutter": {
        "files": ["pubspec.yaml"],
        "content_check": {"pubspec.yaml": "flutter"},
    },
    "spring": {
        "files": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "content_signals": ["spring-boot", "org.springframework"],
    },
    "python": {
        "files": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
    },
}

TESTING_TOOLS = {
    "playwright": {
        "detect": ["playwright.config.ts", "playwright.config.js"],
        "package_json_dep": "@playwright/test",
    },
    "maestro": {
        "detect": [".maestro"],
        "command": "maestro",
    },
    "jest": {
        "detect": ["jest.config.ts", "jest.config.js"],
        "package_json_dep": "jest",
    },
    "vitest": {
        "detect": ["vitest.config.ts", "vitest.config.js"],
        "package_json_dep": "vitest",
    },
    "backstopjs": {
        "detect": ["backstop.json"],
        "package_json_dep": "backstopjs",
    },
    "percy": {
        "package_json_dep": "@percy/cli",
    },
    "paparazzi": {
        "gradle_dep": "app.cash.paparazzi",
    },
    "roborazzi": {
        "gradle_dep": "io.github.takahirom.roborazzi",
    },
    "jacoco": {
        "gradle_dep": "jacoco",
    },
    "espresso": {
        "gradle_dep": "androidx.test.espresso",
    },
    "xctest": {
        "detect_pattern": "XCTest",
    },
    "swift-snapshot-testing": {
        "spm_dep": "swift-snapshot-testing",
    },
    "pytest": {
        "detect": ["pytest.ini", "conftest.py", "pyproject.toml"],
        "pip_dep": "pytest",
    },
}


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, PermissionError):
        return ""


def find_files_recursive(root: Path, name: str, max_depth: int = 6) -> list[Path]:
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        # Skip build/output directories
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", "build", "dist", ".gradle", "Pods", ".build", "__pycache__", "venv", ".venv"}
        ]
        if name in filenames:
            results.append(Path(dirpath) / name)
        for d in list(dirnames):
            if d.endswith(name):
                results.append(Path(dirpath) / d)
    return results


def detect_package_json_deps(root: Path) -> set[str]:
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return set()
    try:
        pkg = json.loads(pkg_path.read_text())
        deps = set(pkg.get("dependencies", {}).keys())
        deps.update(pkg.get("devDependencies", {}).keys())
        return deps
    except (json.JSONDecodeError, OSError):
        return set()


def detect_gradle_deps(root: Path) -> set[str]:
    deps = set()
    for gradle_file in find_files_recursive(root, "build.gradle.kts") + find_files_recursive(root, "build.gradle"):
        content = read_file_safe(gradle_file)
        deps.update(content.split())
    return deps


def detect_platform(project_root: str) -> dict:
    root = Path(project_root).resolve()
    if not root.is_dir():
        return {"error": f"Directory not found: {project_root}"}

    result = {
        "project_root": str(root),
        "platforms": [],
        "frameworks": [],
        "testing_tools": [],
        "missing_tools": [],
        "recommendations": [],
    }

    # Collect deps from root and sub-packages (monorepo support)
    all_pkg_deps: set[str] = set()
    all_pkg_json_paths: list[Path] = []
    for pj in find_files_recursive(root, "package.json", max_depth=3):
        all_pkg_json_paths.append(pj)
        all_pkg_deps.update(detect_package_json_deps(pj.parent))
    # Also include root explicitly
    root_pkg_deps = detect_package_json_deps(root)
    all_pkg_deps.update(root_pkg_deps)

    gradle_content = ""
    for gf in find_files_recursive(root, "build.gradle.kts") + find_files_recursive(root, "build.gradle"):
        gradle_content += read_file_safe(gf) + "\n"

    # Detect platforms
    # React Native / Expo
    if all_pkg_deps & {"react-native", "expo"}:
        result["platforms"].append("react-native")
        if "expo" in all_pkg_deps:
            result["frameworks"].append("Expo")

    # Flutter
    for pubspec in find_files_recursive(root, "pubspec.yaml", max_depth=3):
        if "flutter" in read_file_safe(pubspec):
            result["platforms"].append("flutter")
            break

    # Web — check root and subdirectories for web frameworks
    web_signals = PLATFORM_SIGNALS["web"]["extra_signals"]
    for filename, framework in web_signals.items():
        if find_files_recursive(root, filename, max_depth=3):
            if "web" not in result["platforms"]:
                result["platforms"].append("web")
            result["frameworks"].append(framework)
            break
    if "web" not in result["platforms"] and (all_pkg_deps & {"react", "vue", "angular", "svelte", "next", "express", "fastify"}):
        result["platforms"].append("web")
    # Detect Dockerized web apps (docker-compose with frontend/backend)
    for dc in find_files_recursive(root, "docker-compose.yml", max_depth=3):
        dc_content = read_file_safe(dc)
        if "frontend" in dc_content or "nginx" in dc_content:
            if "web" not in result["platforms"]:
                result["platforms"].append("web")
            if "Docker" not in result["frameworks"]:
                result["frameworks"].append("Docker")
            break

    # Android — search recursively for AndroidManifest.xml
    if find_files_recursive(root, "AndroidManifest.xml"):
        result["platforms"].append("android")
        if "jetpack" in gradle_content.lower() or "compose" in gradle_content.lower():
            result["frameworks"].append("Jetpack Compose")

    # iOS — search recursively for .xcodeproj / .xcworkspace
    ios_detected = False
    for dirpath, dirnames, _ in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth > 4:
            dirnames.clear()
            continue
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", "build", "Pods", ".build"}]
        for d in dirnames:
            if d.endswith(".xcodeproj") or d.endswith(".xcworkspace"):
                ios_detected = True
                break
        if ios_detected:
            break
    if ios_detected:
        result["platforms"].append("ios")
    for spm in find_files_recursive(root, "Package.swift", max_depth=3):
        spm_content = read_file_safe(spm)
        if "SwiftUI" in spm_content:
            result["frameworks"].append("SwiftUI")
        if "ios" not in result["platforms"]:
            result["platforms"].append("ios")
        break

    # Spring
    if "spring-boot" in gradle_content or "org.springframework" in gradle_content:
        result["platforms"].append("spring")
        result["frameworks"].append("Spring Boot")
    else:
        for pom in find_files_recursive(root, "pom.xml", max_depth=3):
            pom_content = read_file_safe(pom)
            if "spring-boot" in pom_content:
                result["platforms"].append("spring")
                result["frameworks"].append("Spring Boot")
                break

    # Python
    for pf in ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]:
        if find_files_recursive(root, pf, max_depth=3):
            if "python" not in result["platforms"]:
                result["platforms"].append("python")
            break

    # Detect existing testing tools
    for tool_name, tool_config in TESTING_TOOLS.items():
        detected = False
        for detect_file in tool_config.get("detect", []):
            if find_files_recursive(root, detect_file, max_depth=3):
                detected = True
                break
        if not detected and "package_json_dep" in tool_config:
            if tool_config["package_json_dep"] in all_pkg_deps:
                detected = True
        if not detected and "gradle_dep" in tool_config:
            if tool_config["gradle_dep"] in gradle_content:
                detected = True
        if not detected and "spm_dep" in tool_config:
            for spm in find_files_recursive(root, "Package.swift", max_depth=3):
                if tool_config["spm_dep"] in read_file_safe(spm):
                    detected = True
                    break
        if detected:
            result["testing_tools"].append(tool_name)

    # Generate recommendations
    platforms = set(result["platforms"])
    tools = set(result["testing_tools"])

    if platforms & {"web", "react-native"} and "playwright" not in tools:
        result["missing_tools"].append("playwright")
        result["recommendations"].append("Install Playwright for web E2E tests: npm init playwright@latest")

    if platforms & {"android", "ios", "react-native", "flutter"} and "maestro" not in tools:
        result["missing_tools"].append("maestro")
        result["recommendations"].append("Install Maestro for mobile E2E tests: curl -fsSL https://get.maestro.mobile.dev | bash")

    if platforms & {"android"} and not (tools & {"paparazzi", "roborazzi"}):
        result["recommendations"].append("Add Paparazzi or Roborazzi for Android snapshot/visual regression tests")

    if platforms & {"ios"} and "swift-snapshot-testing" not in tools:
        result["recommendations"].append("Add swift-snapshot-testing for iOS visual regression tests")

    if platforms & {"web"} and not (tools & {"backstopjs", "percy"}):
        result["recommendations"].append("Consider BackstopJS (free) or Percy (cloud) for web visual regression")

    # Deduplicate
    result["platforms"] = list(dict.fromkeys(result["platforms"]))
    result["frameworks"] = list(dict.fromkeys(result["frameworks"]))

    return result


def print_report(result: dict):
    if "error" in result:
        print(f"ERROR: {result['error']}")
        return

    print("=" * 60)
    print("PROJECT ANALYSIS")
    print("=" * 60)
    print(f"Root: {result['project_root']}")
    print(f"Platforms: {', '.join(result['platforms']) or 'none detected'}")
    print(f"Frameworks: {', '.join(result['frameworks']) or 'none detected'}")
    print()
    print("Testing tools found:")
    if result["testing_tools"]:
        for t in result["testing_tools"]:
            print(f"  + {t}")
    else:
        print("  (none)")
    print()
    if result["missing_tools"]:
        print("Missing tools:")
        for t in result["missing_tools"]:
            print(f"  - {t}")
        print()
    if result["recommendations"]:
        print("Recommendations:")
        for i, r in enumerate(result["recommendations"], 1):
            print(f"  {i}. {r}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    result = detect_platform(project)
    print_report(result)
    # Also output JSON for machine consumption
    print()
    print("JSON:")
    print(json.dumps(result, indent=2))
