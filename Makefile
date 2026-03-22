install:
	pip install -e ".[dev]"

run-api:
	uvicorn apps.api.main:app --reload

run-mcp:
	python -m apps.mcp.server

db-upgrade:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(m)"

test:
	pytest
