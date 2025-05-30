.PHONY: up down migrate seed test lint k6 analytics-export spark-notebook

up:
	docker-compose up --build -d

down:
	docker-compose down

migrate:
	docker-compose exec backend bash -c "poetry run alembic upgrade head"

seed:
	docker-compose exec backend bash -c "poetry run python app/demo/seed.py"

test:
	docker-compose exec backend bash -c "poetry run pytest -q"
	docker-compose exec frontend bash -c "npm test -- --watchAll=false"

lint:
	docker-compose exec backend bash -c "poetry run ruff app && poetry run black --check app && poetry run mypy app --ignore-missing-imports"
	docker-compose exec frontend bash -c "npm run lint"

k6:
	docker-compose exec backend bash -c "node app/demo/k6/script.js"

analytics-export:
	docker-compose exec backend bash -c "poetry run python app/scripts/analytics_export.py --date $${DATE}"

spark-notebook:
	@echo "To run the PySpark notebook locally, execute:"
	@echo "  python analytics/notebooks/OrgRiskTrends.py --date $${DATE:-`date -u +%F`}"

analytics-validate:
	docker-compose exec backend bash -c "python /workspace/analytics/gx/validate.py"