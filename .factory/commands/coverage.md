---
description: Scan project test coverage and report gaps
argument-hint: [module-or-path]
---

Use the subagent `coverage-scanner` to analyze test coverage for this project.

Target: `$ARGUMENTS`

Steps:
1. Detect the project technology stack
2. Run the appropriate coverage tool (JaCoCo, Istanbul/c8, xcov, pytest-cov, go cover)
3. Parse the coverage report
4. Produce a prioritized list of uncovered areas with effort estimates
5. Recommend where to focus next

If a specific module or path is provided, scope the analysis to that area only.
