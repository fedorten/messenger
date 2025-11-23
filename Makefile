.PHONY: help install backend frontend dev docker-up docker-down clean explore

# Путь к Poetry
POETRY = /home/fedor/.local/bin/poetry

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies (Poetry + npm)"
	@echo "  make backend    - Run backend server only"
	@echo "  make frontend   - Run frontend dev server only"
	@echo "  make dev        - Run both backend and frontend"
	@echo "  make docker-up  - Start with Docker Compose"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make clean      - Clean up temporary files"

# Install dependencies
install:
	@echo "Installing backend dependencies with Poetry..."
	cd backend && $(POETRY) install
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Run backend with Poetry
backend:
	@echo "Starting backend server on http://localhost:8000"
	@echo "API docs: http://localhost:8000/docs"
	cd backend && $(POETRY) run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend
frontend:
	@echo "Starting frontend dev server on http://localhost:3000"
	cd frontend && npm run dev

# Run both backend and frontend in parallel
dev:
	@echo "Starting both backend and frontend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill 0' EXIT; \
	cd backend && $(POETRY) run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd frontend && npm run dev & \
	wait

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete