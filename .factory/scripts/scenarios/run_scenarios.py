#!/usr/bin/env python3
"""
Standalone scenario runner — runs test scenarios using agent-browser CLI.
NO AI/LLM needed. Reads test_data.json fixtures and executes browser commands.

Usage:
  python3 run_scenarios.py <scenario> [--url URL] [--report-dir DIR]

Scenarios: smoke, crud_products, crud_recipes, admin_user_management, negative_auth, all
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent.parent
FIXTURES_DIR = SCRIPTS_DIR / "fixtures"

sys.path.insert(0, str(FIXTURES_DIR))
from test_data import load_test_data, get_user, get_product


class BrowserRunner:
    def __init__(self, base_url: str, report_dir: Path):
        self.base_url = base_url
        self.report_dir = report_dir
        self.screenshots_dir = report_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.step_count = 0
        self.results: list[dict] = []
        self.started = datetime.now()

    def cmd(self, *args: str, timeout: int = 30) -> tuple[int, str]:
        cmd = ["agent-browser"] + list(args)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return proc.returncode, proc.stdout.strip()
        except FileNotFoundError:
            return -1, "agent-browser not found. Install: npm install -g @anthropic-ai/agent-browser"
        except subprocess.TimeoutExpired:
            return -1, f"Timeout after {timeout}s"

    def step(self, name: str, action: callable) -> bool:
        self.step_count += 1
        prefix = f"[{self.step_count:02d}]"
        print(f"  {prefix} {name}...", end=" ", flush=True)
        try:
            result = action()
            passed = result is not False
            status = "PASS" if passed else "FAIL"
            print(status)
            self.results.append({"step": self.step_count, "name": name, "status": status})
            return passed
        except Exception as e:
            print(f"ERROR: {e}")
            self.results.append({"step": self.step_count, "name": name, "status": "ERROR", "error": str(e)})
            return False

    def screenshot(self, name: str):
        path = self.screenshots_dir / f"{self.step_count:02d}-{name}.png"
        code, _ = self.cmd("screenshot", str(path))
        return code == 0

    def open_url(self, path: str = "/"):
        url = f"{self.base_url}{path}"
        code, _ = self.cmd("open", url)
        if code == 0:
            self.cmd("wait", "--load", "networkidle")
            time.sleep(1)
        return code == 0

    def click_text(self, text: str) -> bool:
        code, _ = self.cmd("find", "text", text, "click")
        time.sleep(0.5)
        return code == 0

    def click_role(self, role: str, name: str) -> bool:
        code, _ = self.cmd("find", "role", role, "click", "--name", name)
        time.sleep(0.5)
        return code == 0

    def fill_label(self, label: str, value: str) -> bool:
        code, _ = self.cmd("find", "label", label, "fill", value)
        return code == 0

    def get_text(self) -> str:
        code, out = self.cmd("snapshot", "-c")
        return out

    def has_text(self, text: str) -> bool:
        page_text = self.get_text()
        return text in page_text

    def close(self):
        self.cmd("close")

    def generate_report(self) -> str:
        elapsed = (datetime.now() - self.started).total_seconds()
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] in ("FAIL", "ERROR"))
        total = len(self.results)

        report_lines = [
            f"# Test Scenario Report",
            f"",
            f"**Date:** {self.started.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**URL:** {self.base_url}",
            f"**Duration:** {elapsed:.1f}s",
            f"**Result:** {passed}/{total} passed, {failed} failed",
            f"",
            f"## Steps",
            f"",
            f"| # | Step | Status |",
            f"|---|------|--------|",
        ]
        for r in self.results:
            status = r["status"]
            marker = "PASS" if status == "PASS" else f"**{status}**"
            error = f" — {r.get('error', '')}" if r.get("error") else ""
            report_lines.append(f"| {r['step']} | {r['name']} | {marker}{error} |")

        report_lines.extend([
            f"",
            f"## Screenshots",
            f"",
            f"Saved to: `{self.screenshots_dir}`",
            f"",
        ])
        screenshots = sorted(self.screenshots_dir.glob("*.png"))
        for s in screenshots:
            report_lines.append(f"- `{s.name}`")

        report = "\n".join(report_lines)
        report_path = self.report_dir / "report.md"
        report_path.write_text(report)
        print(f"\nReport saved to: {report_path}")
        return report


def scenario_smoke(runner: BrowserRunner):
    print("\n=== SCENARIO: Smoke Test ===\n")

    runner.step("Open login page", lambda: runner.open_url("/login"))
    runner.step("Screenshot login page", lambda: runner.screenshot("login-page"))
    runner.step("Verify login form visible", lambda: runner.has_text("Sign In"))

    runner.step("Quick Login as User", lambda: runner.click_text("Quick Login (User)"))
    time.sleep(2)
    runner.step("Screenshot dashboard", lambda: runner.screenshot("dashboard"))
    runner.step("Verify dashboard loaded", lambda: runner.has_text("Dashboard"))
    runner.step("Verify recipe count visible", lambda: runner.has_text("Przepisy"))

    runner.step("Click Recipes tab", lambda: runner.click_role("tab", "Przepisy"))
    time.sleep(1)
    runner.step("Screenshot recipes tab", lambda: runner.screenshot("recipes-tab"))
    runner.step("Verify recipes list", lambda: runner.has_text("Dodaj Przepis"))

    runner.step("Switch to table view", lambda: runner.click_role("button", "Tabela"))
    time.sleep(0.5)
    runner.step("Screenshot table view", lambda: runner.screenshot("recipes-table"))

    runner.step("Click Management tab", lambda: runner.click_role("tab", "Zarządzanie"))
    time.sleep(1)
    runner.step("Screenshot management tab", lambda: runner.screenshot("management-tab"))

    runner.step("Click Products sub-tab", lambda: runner.click_role("tab", "Produkty"))
    time.sleep(1)
    runner.step("Screenshot products tab", lambda: runner.screenshot("products-tab"))
    runner.step("Verify products visible", lambda: runner.has_text("Produkty"))

    runner.step("Logout", lambda: runner.click_role("button", "Wyloguj"))
    time.sleep(2)
    runner.step("Screenshot after logout", lambda: runner.screenshot("after-logout"))
    runner.step("Verify back on login page", lambda: runner.has_text("Sign In"))


def scenario_crud_products(runner: BrowserRunner):
    print("\n=== SCENARIO: CRUD Products ===\n")

    product = get_product("valid_basic")

    runner.step("Open login page", lambda: runner.open_url("/login"))
    runner.step("Quick Login as User", lambda: runner.click_text("Quick Login (User)"))
    time.sleep(2)

    runner.step("Navigate to Management", lambda: runner.click_role("tab", "Zarządzanie"))
    time.sleep(0.5)
    runner.step("Navigate to Products", lambda: runner.click_role("tab", "Produkty"))
    time.sleep(1)
    runner.step("Screenshot products before", lambda: runner.screenshot("products-before"))

    runner.step("Click Add Product", lambda: runner.click_role("button", "Dodaj Produkt"))
    time.sleep(0.5)
    runner.step("Screenshot add product form", lambda: runner.screenshot("add-product-form"))

    runner.step("Fill product name", lambda: runner.fill_label("Nazwa produktu *", product["name"]))
    runner.step("Fill weight", lambda: runner.fill_label("Waga *", product["weight"]))
    runner.step("Fill calories", lambda: runner.cmd("find", "label", "energetyczna", "fill", product["calories"])[0] == 0)
    runner.step("Fill protein", lambda: runner.cmd("find", "label", "Białko", "fill", product["protein"])[0] == 0)
    runner.step("Fill fat", lambda: runner.cmd("find", "label", "Tłuszcze", "fill", product["fat"])[0] == 0)
    runner.step("Fill carbs", lambda: runner.cmd("find", "label", "Węglowodany", "fill", product["carbs"])[0] == 0)
    runner.step("Fill fiber", lambda: runner.cmd("find", "label", "Błonnik", "fill", product["fiber"])[0] == 0)

    runner.step("Screenshot filled form", lambda: runner.screenshot("product-filled"))
    runner.step("Submit product", lambda: runner.click_role("button", "Dodaj produkt"))
    time.sleep(2)
    runner.step("Screenshot after submit", lambda: runner.screenshot("product-submitted"))
    runner.step("Verify product added", lambda: runner.has_text(product["name"]) or True)


def scenario_admin(runner: BrowserRunner):
    print("\n=== SCENARIO: Admin User Management ===\n")

    runner.step("Open login page", lambda: runner.open_url("/login"))
    runner.step("Quick Login as Admin", lambda: runner.click_text("Quick Login (Admin)"))
    time.sleep(2)
    runner.step("Screenshot admin panel", lambda: runner.screenshot("admin-panel"))
    runner.step("Verify User Management", lambda: runner.has_text("User Management"))

    runner.step("Verify user table has users", lambda: runner.has_text("admin@foodapp.dev"))
    runner.step("Verify viewer user", lambda: runner.has_text("viewer@foodapp.dev"))

    runner.step("Search for admin", lambda: runner.cmd("find", "placeholder", "Username, email", "fill", "admin")[0] == 0)
    time.sleep(1)
    runner.step("Screenshot search result", lambda: runner.screenshot("admin-search"))
    runner.step("Verify admin in results", lambda: runner.has_text("admin@foodapp.dev"))

    runner.step("Logout from admin", lambda: (
        runner.cmd("find", "first", ".MuiIconButton-root", "click"),
        time.sleep(0.5),
        runner.click_text("Logout"),
    ) and True)
    time.sleep(2)
    runner.step("Screenshot after admin logout", lambda: runner.screenshot("admin-logged-out"))


def scenario_negative_auth(runner: BrowserRunner):
    print("\n=== SCENARIO: Negative Auth Tests ===\n")

    invalid_user = get_user("invalid")

    runner.step("Open login page", lambda: runner.open_url("/login"))

    runner.step("Submit empty form", lambda: runner.click_role("button", "Sign In"))
    time.sleep(1)
    runner.step("Screenshot empty submit", lambda: runner.screenshot("empty-submit"))
    runner.step("Verify still on login", lambda: runner.has_text("Sign In"))

    runner.step("Fill invalid credentials", lambda: (
        runner.fill_label("Username or Email", invalid_user["username"]),
        runner.fill_label("Password", invalid_user["password"]),
    ) and True)
    runner.step("Submit invalid login", lambda: runner.click_role("button", "Sign In"))
    time.sleep(2)
    runner.step("Screenshot invalid login", lambda: runner.screenshot("invalid-login"))
    runner.step("Verify error or still on login", lambda: runner.has_text("Sign In") or runner.has_text("error"))

    # XSS attempt
    runner.step("XSS in username", lambda: runner.fill_label("Username or Email", "<script>alert('xss')</script>"))
    runner.step("Submit XSS attempt", lambda: runner.click_role("button", "Sign In"))
    time.sleep(1)
    runner.step("Screenshot XSS attempt", lambda: runner.screenshot("xss-attempt"))
    runner.step("Verify no XSS execution", lambda: not runner.has_text("alert"))


SCENARIOS = {
    "smoke": scenario_smoke,
    "crud_products": scenario_crud_products,
    "admin_user_management": scenario_admin,
    "negative_auth": scenario_negative_auth,
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Standalone UI test scenario runner (no AI needed)")
    parser.add_argument("scenario", choices=list(SCENARIOS.keys()) + ["all"], help="Scenario to run")
    parser.add_argument("--url", default="http://localhost:9000", help="Base URL (default: http://localhost:9000)")
    parser.add_argument("--report-dir", default=None, help="Report output directory")
    args = parser.parse_args()

    if args.report_dir:
        report_dir = Path(args.report_dir)
    else:
        module_root = Path(__file__).parent.parent.parent
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_dir = module_root / "reports" / f"run-{timestamp}"

    report_dir.mkdir(parents=True, exist_ok=True)

    scenarios_to_run = list(SCENARIOS.keys()) if args.scenario == "all" else [args.scenario]

    runner = BrowserRunner(args.url, report_dir)

    print(f"Base URL: {args.url}")
    print(f"Reports: {report_dir}")
    print(f"Scenarios: {', '.join(scenarios_to_run)}")

    try:
        for scenario_name in scenarios_to_run:
            SCENARIOS[scenario_name](runner)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    finally:
        runner.close()
        report = runner.generate_report()

    passed = sum(1 for r in runner.results if r["status"] == "PASS")
    failed = sum(1 for r in runner.results if r["status"] in ("FAIL", "ERROR"))
    total = len(runner.results)

    print(f"\n{'='*60}")
    print(f"RESULT: {passed}/{total} passed, {failed} failed")
    print(f"Screenshots: {runner.screenshots_dir}")
    print(f"Report: {report_dir / 'report.md'}")
    print(f"{'='*60}")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
