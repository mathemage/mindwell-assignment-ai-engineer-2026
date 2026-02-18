.PHONY: help dev install test lint format migrate seed clean docker-up docker-down

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	cd backend && pip install -e .[dev]

dev: ## Run development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	cd backend && pytest

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linter
	cd backend && ruff check app/

format: ## Format code
	cd backend && ruff format app/

typecheck: ## Run type checker
	cd backend && mypy app/

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="your message")
	cd backend && alembic revision --autogenerate -m "$(MESSAGE)"

seed: ## Seed database with sample data
	cd backend && python -m app.scripts.seed_data

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

docker-up: ## Start docker services
	docker-compose up -d

docker-down: ## Stop docker services
	docker-compose down

docker-build: ## Build docker images
	docker-compose build

docker-logs: ## View docker logs
	docker-compose logs -f

pre-commit: ## Set up pre-commit hooks
	pre-commit install

ci: lint typecheck test ## Run all CI checks
