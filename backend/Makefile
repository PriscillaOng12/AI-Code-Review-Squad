.PHONY: up down migrate seed test lint k6 analytics-export spark-notebook

up:
	docker-compose -f ../docker-compose.yml up --build -d

down:
	docker-compose -f ../docker-compose.yml down

migrate:
	poetry run alembic upgrade head

seed:
	poetry run python app/demo/seed.py

test:
	poetry run pytest -q

lint:
	poetry run ruff app
	poetry run black --check app
	poetry run mypy app --ignore-missing-imports

k6:
	node app/demo/k6/script.js

analytics-export:
	poetry run python app/scripts/analytics_export.py --date $${DATE}

spark-notebook:
	@echo "To run the PySpark notebook, execute the following commands:"
	@echo "  python analytics/notebooks/OrgRiskTrends.py --date $${DATE:-`date -u +%F`}"