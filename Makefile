# Makefile для Django_Delivery_service проекта
# Работает на Windows и Linux, а также внутри Docker контейнера

.PHONY: help install lint fmt type security cc check run test migrate shell docker-build docker-run docker-up docker-down

# Определяем окружение
ifeq ($(INSIDE_CONTAINER),true)
    # Внутри контейнера: poetry установлен глобально
    POETRY_RUN := poetry run
    PYTHON := python
else
    # На хосте: используем .venv
    VENV := .venv
    ifeq ($(OS),Windows_NT)
        PYTHON := $(VENV)/Scripts/python.exe
    else
        PYTHON := $(VENV)/bin/python
    endif
    POETRY_RUN := $(PYTHON) -m poetry run
endif

# Путь к manage.py (теперь в src/)
MANAGE_PY := src/manage.py

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make lint           - Ruff check"
	@echo "  make fmt            - Ruff format"
	@echo "  make type           - Mypy type check"
	@echo "  make security       - Bandit security"
	@echo "  make cc             - Radon complexity"
	@echo "  make check          - Run all checks"
	@echo "  make run            - Run Django server"
	@echo "  make test           - Run pytest"
	@echo "  make migrate        - Run Django migrations"
	@echo "  make makemigrations - Create Django migrations"
	@echo "  make shell          - Django shell"
	@echo "  make superuser      - Create superuser"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make docker-up      - Docker compose up"
	@echo "  make docker-down    - Docker compose down"

install:
	poetry install

lint:
	$(POETRY_RUN) ruff check . --fix

fmt:
	$(POETRY_RUN) ruff format .

type:
	$(POETRY_RUN) mypy src/ apps/

security:
	$(POETRY_RUN) bandit -r src/ apps/ -s B311,B324

cc:
	$(POETRY_RUN) radon cc src/ apps/ -s -a

check:
	@echo "Running lint..."
	$(POETRY_RUN) ruff check . --fix
	@echo ""
	@echo "Running type check..."
	-$(POETRY_RUN) mypy src/ apps/
	@echo ""
	@echo "Running security check..."
	-$(POETRY_RUN) bandit -r src/ apps/ -s B311,B324
	@echo ""
	@echo "Running complexity analysis..."
	-$(POETRY_RUN) radon cc src/ apps/ -s -a
	@echo ""
	@echo "All checks passed!"

run:
	python $(MANAGE_PY) runserver

test:
	$(POETRY_RUN) pytest -v

migrate:
	python $(MANAGE_PY) migrate

makemigrations:
	python $(MANAGE_PY) makemigrations

shell:
	python $(MANAGE_PY) shell

superuser:
	python $(MANAGE_PY) createsuperuser

docker-build:
	docker build -t delivery_service:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env delivery_service:latest

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down