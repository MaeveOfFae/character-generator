.PHONY: help docs docs-serve test test-fast test-coverage clean install-dev migrate-drafts

help:
	@echo "Character Generator - Available Commands:"
	@echo ""
	@echo "  make docs           Generate API documentation"
	@echo "  make docs-serve     Generate docs and serve locally"
	@echo "  make test           Run all tests with coverage"
	@echo "  make test-fast      Run tests (skip slow integration tests)"
	@echo "  make test-coverage  Run tests and open coverage report"
	@echo "  make clean          Clean generated files"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make migrate-drafts Migrate existing drafts to include metadata"
	@echo ""

docs:
	@echo "Generating API documentation..."
	@python tools/generate_docs.py

docs-serve: docs
	@echo "Starting local documentation server..."
	@echo "Open http://localhost:8000 in your browser"
	@python -m http.server --directory docs/api/bpui 8000

test:
	@echo "Running all tests with coverage..."
	@pytest

test-fast:
	@echo "Running fast tests (skipping slow integration tests)..."
	@pytest -m "not slow"

test-coverage: test
	@echo "Opening coverage report..."
	@xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Coverage report at: htmlcov/index.html"

clean:
	@echo "Cleaning generated files..."
	@rm -rf htmlcov/
	@rm -rf docs/api/bpui/
	@rm -rf .pytest_cache/
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Clean complete"

install-dev:
	@echo "Installing development dependencies..."
	@pip install -r requirements-dev.txt
	@echo "✓ Development dependencies installed"

migrate-drafts:
	@echo "Migrating existing drafts..."
	@python tools/migrate_existing_drafts.py
