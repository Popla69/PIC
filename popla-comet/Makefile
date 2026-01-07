.PHONY: help install-backend install-android test-backend test-android lint-backend lint-android clean docker-up docker-down

help:
	@echo "Popla Comet - Development Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install-backend    - Install backend dependencies"
	@echo "  make install-android    - Setup Android project"
	@echo ""
	@echo "Development Commands:"
	@echo "  make run-backend        - Run backend development server"
	@echo "  make run-android        - Build and install Android app"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test-backend       - Run backend tests"
	@echo "  make test-android       - Run Android tests"
	@echo "  make test-all           - Run all tests"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  make lint-backend       - Lint backend code"
	@echo "  make format-backend     - Format backend code"
	@echo "  make lint-android       - Lint Android code"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up          - Start all services with Docker"
	@echo "  make docker-down        - Stop all services"
	@echo "  make docker-logs        - View Docker logs"
	@echo ""
	@echo "Cleanup Commands:"
	@echo "  make clean              - Clean build artifacts"
	@echo "  make clean-all          - Deep clean (including deps)"

# Backend Commands
install-backend:
	cd backend && python -m venv venv && \
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt

run-backend:
	cd backend && \
	. venv/bin/activate && \
	python -m app.main

test-backend:
	cd backend && \
	. venv/bin/activate && \
	pytest -v

lint-backend:
	cd backend && \
	. venv/bin/activate && \
	ruff check . && \
	mypy app

format-backend:
	cd backend && \
	. venv/bin/activate && \
	black . && \
	ruff check --fix .

# Android Commands
install-android:
	@echo "Open android-app in Android Studio to sync dependencies"

run-android:
	cd android-app && ./gradlew installDebug

test-android:
	cd android-app && ./gradlew test

lint-android:
	cd android-app && ./gradlew lint

# Combined Commands
test-all: test-backend test-android

# Docker Commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-rebuild:
	docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Cleanup Commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	cd android-app && ./gradlew clean 2>/dev/null || true

clean-all: clean
	rm -rf backend/venv
	rm -rf backend/.venv
	cd android-app && rm -rf .gradle build || true

# Environment setup
setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi
