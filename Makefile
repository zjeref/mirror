.PHONY: dev test migrate lint setup

# Backend
dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && python -m pytest tests/ -v --cov=app

test-quick:
	cd backend && python -m pytest tests/ -x -q

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision --autogenerate -m "$(msg)"

lint:
	cd backend && ruff check app/ tests/

format:
	cd backend && ruff format app/ tests/

# Setup
setup:
	cd backend && pip install -e ".[dev]"
	mkdir -p data
