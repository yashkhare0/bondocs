.PHONY: install test format lint precommit clean fix

# Install dependencies
install:
	poetry install

# Run tests
test:
	poetry run pytest

# Format code with Black and Ruff
format:
	poetry run black .
	poetry run ruff check --fix .

# Apply code fixes with Ruff only
fix:
	poetry run ruff check . --fix

# Lint code with Ruff
lint:
	poetry run ruff check .
	poetry run mypy .

# Install pre-commit hooks
precommit:
	poetry run pre-commit install
	poetry run pre-commit autoupdate

# Run pre-commit on all files
precommit-all:
	poetry run pre-commit run --all-files

# Clean up cache directories
clean:
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Default target is to run tests
all: format lint test
