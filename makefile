.PHONY: dev test lint format

dev:
	@echo "Starting development server..."
	cd api && \
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .