.PHONY: install dev test eval docker deploy seed-inventory lint typecheck

install:
	pip install -r requirements.txt

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=src --cov-report=term-missing --cov-fail-under=80

eval:
	python evals/run_goldens.py

docker:
	docker build -t lyra .

deploy:
	fly deploy

seed-inventory:
	python scripts/seed_hillz.py

lint:
	ruff check src/ tests/ evals/
	black --check src/ tests/ evals/

typecheck:
	mypy --strict src/

format:
	black src/ tests/ evals/ scripts/
	ruff check --fix src/ tests/ evals/
