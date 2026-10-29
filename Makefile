COMPOSE ?= docker compose
BASE = $(COMPOSE) -f compose.yaml
DEMO = $(BASE) -f compose.ngrok.yaml
DEPLOY_FLAGS = --build --force-recreate --always-recreate-deps --wait --wait-timeout 180

.PHONY: help test deploy demo status logs down

help:
	@echo "make test    Run the complete backend test suite in Docker"
	@echo "make deploy  Rerun tests, then start the backend and website gateway"
	@echo "make demo    Rerun tests, then share the website through ngrok"
	@echo "make status  Show service status, including the finished test job"
	@echo "make logs    Show recent gateway, backend, and test logs"
	@echo "make down    Remove this project's containers; keep the database volume"

test:
	$(BASE) up --build --force-recreate --exit-code-from tests tests

deploy:
	$(BASE) up $(DEPLOY_FLAGS) web

demo:
	$(DEMO) up $(DEPLOY_FLAGS) ngrok

status:
	$(BASE) ps --all

logs:
	$(BASE) logs --tail=100

down:
	$(BASE) down --remove-orphans
