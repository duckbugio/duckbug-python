init: docker-down-clear \
	docker-pull docker-build docker-up

up: docker-up
down: docker-down
restart: down up

docker-up:
	docker compose up -d

docker-down:
	docker compose down --remove-orphans

docker-down-clear:
	docker compose down -v --remove-orphans

docker-pull:
	docker compose pull

docker-build:
	docker compose build --pull

var:
	mkdir -p var/cache

check: lint analyze test

lint: var
	docker compose run --rm python-cli ruff check .
	docker compose run --rm python-cli ruff format --check .

lint-fix: var
	docker compose run --rm python-cli ruff check --fix .
	docker compose run --rm python-cli ruff format .

analyze: var
	docker compose run --rm python-cli mypy

test: var
	docker compose run --rm python-cli python -m unittest discover -s tests -p 'test_*.py'

clean:
	rm -rf var/cache __pycache__ .mypy_cache .ruff_cache .pytest_cache build dist *.egg-info

.PHONY: init up down restart docker-up docker-down docker-down-clear docker-pull docker-build var check lint lint-fix analyze test clean
