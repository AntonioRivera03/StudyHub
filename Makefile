.PHONY: setup server ui build run check

setup:
	cd Server && uv sync
	npm --prefix UI install

server:
	cd Server && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

ui:
	npm --prefix UI run dev -- --host 127.0.0.1

build:
	npm --prefix UI run build

run: build
	cd Server && STUDYHUB_ENVIRONMENT=production uv run uvicorn app.main:app --host 127.0.0.1 --port 8000

check:
	cd Server && uv run ruff check .
	cd Server && uv run ruff format --check .
	cd Server && uv run mypy app
	cd Server && uv run pytest
	npm --prefix UI run lint
	npm --prefix UI run typecheck
	npm --prefix UI test -- --run
	npm --prefix UI run build
	npm --prefix UI run e2e
