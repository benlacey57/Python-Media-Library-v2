.PHONY: help install test lint format security check

help:
	@echo "Available commands:"
	@echo "  make install  - Install project dependencies"
	@echo "  make test     - Run pytest test suite"
	@echo "  make lint     - Run flake8 linter check"
	@echo "  make format   - Run black code formatter"
	@echo "  make security - Run bandit security scan"
	@echo "  make check    - Run format, lint, security, and tests sequentially"

install:
	pip install --upgrade pip
	pip install -r requirements-dev.txt

test:
	PYTHONPATH=src python -m pytest

lint:
	flake8 src/ tests/

format:
	black src/ tests/

security:
	bandit -r src/core src/modules -ll

check: format lint security test
