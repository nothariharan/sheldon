.PHONY: setup test lint smoke

setup:
	./scripts/setup.sh

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check sheldon tests

smoke:
	.venv/bin/python -m pytest tests/test_smoke.py
