.PHONY: install dev down seed test lint typecheck eval demo migrate clean

# Local Python deps via uv. Run inside an activated .venv
# (see README "Local path"). Falls back to pip if uv is not installed.
install:
	@if command -v uv >/dev/null 2>&1; then \
		uv pip install -e ".[dev]"; \
	else \
		echo "[install] uv not found; falling back to pip"; \
		pip install -e ".[dev]"; \
	fi

dev:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose run --rm app alembic upgrade head

seed: migrate
	docker compose run --rm app python -m scripts.seed

test:
	pytest -q

lint:
	ruff check app tests scripts
	lint-imports

typecheck:
	mypy app

eval:
	python -m app.extraction.eval.runner

demo:
	python -m scripts.demo_extract app/extraction/eval/golden/sample_submittal.pdf

clean:
	docker compose down -v
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__
