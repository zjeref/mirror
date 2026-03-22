PYTHON ?= /home/davion/anaconda3/envs/evi-env/bin/python

.PHONY: dev test test-quick lint format setup

dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && $(PYTHON) -m pytest tests/ -v

test-quick:
	cd backend && $(PYTHON) -m pytest tests/ -x -q

lint:
	cd backend && $(PYTHON) -m ruff check app/ tests/

format:
	cd backend && $(PYTHON) -m ruff format app/ tests/

setup:
	cd backend && $(PYTHON) -m pip install -e ".[dev]"
