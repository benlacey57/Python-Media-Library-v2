.PHONY: help install test lint format security check

help:
	@echo "Available commands:"
	@echo "  make install  - Install project dependencies"
	@echo "  make test     - Run pytest test suite"
	@echo "  make lint     - Run ruff linter check"
	@echo "  make format   - Run ruff code formatter"
	@echo "  make security - Run bandit security scan"
	@echo "  make check    - Run format, lint, security, and tests sequentially"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest -v

lint:
	ruff check .

format:
	ruff format .

security:
	bandit -r core modules -ll

check: format lint security test

