PORT ?= 8000

.DEFAULT_GOAL := help
.PHONY: help run shell migrations migrate test clean check

help:  ## list the targets
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## /\t/' | expand -t 12

run:  ## development server on PORT (default 8000) — the same ASGI server the unit runs
	uv run uvicorn root.asgi:application --reload --port $(PORT)

shell:  ## django shell
	uv run manage.py shell

migrations:  ## generate migrations — read the file before applying it
	uv run manage.py makemigrations

migrate:  ## apply migrations
	uv run manage.py migrate

test:  ## the whole test suite
	uv run pytest

clean:  ## remove every __pycache__ outside .venv
	./scripts/clean-pycache.sh

check:  ## everything that must pass before a commit
	uv run manage.py check
	uv run manage.py makemigrations --check --dry-run
	uv run pytest -q
	./scripts/check-docs.sh
