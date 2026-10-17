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
	python -m pytest

lint:
	flake8 .

format:
	black .

security:
	bandit -r core modules -ll

check: format lint security test
