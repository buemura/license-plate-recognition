.PHONY: help install dev api worker migrate migrate-create docker-up docker-down docker-build docker-logs clean

# Default target
help:
	@echo "License Plate Recognition - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make dev            - Start API server and worker (requires Redis & PostgreSQL)"
	@echo "  make api            - Start FastAPI server only"
	@echo "  make worker         - Start Celery worker only"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration (use MSG='description')"
	@echo "  make migrate-down   - Rollback one migration"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      - Start all services with Docker"
	@echo "  make docker-down    - Stop all Docker services"
	@echo "  make docker-build   - Rebuild Docker images"
	@echo "  make docker-logs    - View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Remove cache and temporary files"
	@echo "  make test-upload    - Test image upload with sample image"

# Install dependencies
install:
	pip install -r requirements.txt

# Start API server (development)
api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker
worker:
	celery -A app.worker.celery_app worker --loglevel=info

# Start both API and worker (requires running in separate terminals or use docker)
dev:
	@echo "Starting API server and worker..."
	@echo "Run 'make api' in one terminal and 'make worker' in another"
	@echo "Or use 'make docker-up' to start everything with Docker"

# Database migrations
migrate:
	alembic upgrade head

migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate-create MSG='migration description'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(MSG)"

migrate-down:
	alembic downgrade -1

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Test upload with sample image
test-upload:
	@if [ -f "images/placa1.jpg" ]; then \
		curl -X POST http://localhost:8000/api/v1/recognition -F "file=@images/placa1.jpg"; \
	else \
		echo "Sample image not found. Provide an image path:"; \
		echo "  curl -X POST http://localhost:8000/api/v1/recognition -F 'file=@your_image.jpg'"; \
	fi
