.PHONY: dev down seed test lint typecheck eval demo migrate clean

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
