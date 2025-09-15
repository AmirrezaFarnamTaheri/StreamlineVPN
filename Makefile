SHELL := /bin/sh

.PHONY: dev-up dev-down prod-up prod-down validate

dev-up:
	docker compose -f docker-compose.dev.yml up -d --build

dev-down:
	docker compose -f docker-compose.dev.yml down -v

prod-up:
	docker compose -f docker-compose.production.yml up -d --build

prod-down:
	docker compose -f docker-compose.production.yml down -v

validate:
	python scripts/comprehensive_validator.py

