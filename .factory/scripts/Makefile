# UI Test Runner — Makefile shortcuts
# Usage: make <target> [PROJECT=/path/to/project]

PROJECT ?= $(shell pwd)
RUNNER  := python3 $(dir $(abspath $(lastword $(MAKEFILE_LIST))))test-runner.py

.PHONY: help detect setup coverage generate run \
        visual-setup visual-capture visual-compare visual-update \
        maestro-init maestro-run maestro-list \
        screenshot report install-node

help: ## Show this help
	@echo "UI Test Runner — available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Set PROJECT=/path/to/project to target a specific project."

# === Detection & Setup ===

detect: ## Detect project platform and testing tools
	$(RUNNER) detect $(PROJECT)

setup: ## Install and configure testing tools for the project
	$(RUNNER) setup $(PROJECT)

# === Testing ===

coverage: ## Run test coverage analysis
	$(RUNNER) coverage $(PROJECT)

generate: ## Generate E2E test boilerplate
	$(RUNNER) generate $(PROJECT)

run: ## Run all E2E tests (Playwright + Maestro)
	$(RUNNER) run $(PROJECT)

# === Visual Regression ===

visual-setup: ## Set up visual regression infrastructure
	$(RUNNER) visual setup $(PROJECT)

visual-capture: ## Capture baseline screenshots
	$(RUNNER) visual capture $(PROJECT)

visual-compare: ## Compare screenshots against baselines
	$(RUNNER) visual compare $(PROJECT)

visual-update: ## Accept current screenshots as new baselines
	$(RUNNER) visual update $(PROJECT)

# === Maestro (Mobile) ===

maestro-init: ## Initialize Maestro flow directory
	$(RUNNER) maestro init $(PROJECT)

maestro-run: ## Run all Maestro flows
	$(RUNNER) maestro run $(PROJECT)

maestro-list: ## List all Maestro flows
	$(RUNNER) maestro list $(PROJECT)

# === Utilities ===

screenshot: ## Take a screenshot (usage: make screenshot URL=http://...)
	$(RUNNER) screenshot $(URL)

report: ## Show testing status report
	$(RUNNER) report $(PROJECT)

install-node: ## Install Node.js dependencies for screenshot/diff tools
	cd $(dir $(abspath $(lastword $(MAKEFILE_LIST))))scripts/node && npm install
