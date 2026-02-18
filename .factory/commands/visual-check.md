---
description: Visual regression testing — capture screenshot baselines, compare diffs, manage visual test infrastructure
argument-hint: <setup|capture|compare|update> [page-or-screen]
---

Use the subagent `visual-regression` to manage visual regression testing for this project.

Action: `$ARGUMENTS`

If no action is specified, do the following:
1. Detect the platform and existing visual testing setup
2. Report current visual baseline status (how many screenshots, what's covered)
3. Suggest missing visual test coverage
4. Ask what to do next

If an action is specified:
- `setup` — install and configure visual regression tooling (Playwright screenshots / BackstopJS / Paparazzi / swift-snapshot-testing)
- `capture <page>` — capture baseline screenshots for a specific page/screen or all pages
- `compare` — run visual comparison against existing baselines and report diffs
- `update` — accept current screenshots as new baselines after intentional UI changes
