---
description: Run the test-master droid to scan, generate, or manage tests
argument-hint: <scan|generate|review|api|mock> [target-path]
---

Use the subagent `test-master` to work on tests for this project.

Action: `$ARGUMENTS`

If no action is specified, do the following:
1. Detect the project stack
2. Run a coverage scan
3. Report the top uncovered areas
4. Ask what to do next (generate tests, review existing tests, create mock data, or test APIs)

If an action is specified:
- `scan` or `coverage` — run coverage-scanner and produce a gap report
- `generate <path>` — generate tests for the specified file, class, module, or the whole project if no path given
- `review` — audit existing test quality with test-reviewer
- `api` — generate API/integration tests with api-tester
- `mock <path>` — generate mock data and fixtures for the models at the given path
