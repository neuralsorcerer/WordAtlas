.PHONY: run web test lint format install-dev typecheck

run:
	python -m wordatlas.cli list happiness --depth 1

web:
	wordatlas web --host 0.0.0.0 --port 8000 --reload

install-dev:
	pip install -e .[dev]

test:
	pytest -q

lint:
	ruff check .
	typecheck

format:
	black .
	ruff check . --fix

typecheck:
	mypy wordatlas