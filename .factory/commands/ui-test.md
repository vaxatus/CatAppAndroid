---
description: Generate E2E UI tests — detects platform (Web/Android/iOS), generates Playwright or Maestro tests
argument-hint: <scan|generate|setup> [target-page-or-flow]
---

Use the subagent `ui-test-master` to work on UI end-to-end tests for this project.

Action: `$ARGUMENTS`

If no action is specified, do the following:
1. Detect the project platform (Web, Android, iOS, React Native, Flutter)
2. Check if E2E testing tools are installed (Playwright for web, Maestro for mobile)
3. Scan existing UI tests and report coverage
4. Recommend next steps

If an action is specified:
- `scan` — inventory existing UI tests, identify untested screens/flows
- `generate <target>` — generate E2E tests for a specific page/screen/flow, or "all" for the full app
- `setup` — install and configure the testing tools for the detected platform
- `smoke` — generate a critical-path smoke test covering login through main feature
