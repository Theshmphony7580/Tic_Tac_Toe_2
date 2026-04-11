.PHONY: up down logs restart db-reset seed test lint

up:
	docker compose -f core-infrastructure/docker-compose.yml up -d

down:
	docker compose -f core-infrastructure/docker-compose.yml down

logs:
	docker compose -f core-infrastructure/docker-compose.yml logs -f

restart: down up

db-reset:
	docker compose -f core-infrastructure/docker-compose.yml down -v
	docker compose -f core-infrastructure/docker-compose.yml up -d postgres redis

seed:
	docker exec -i $$(docker compose -f core-infrastructure/docker-compose.yml ps -q postgres) psql -U admin -d talentintel -f /docker-entrypoint-initdb.d/02-seed.sql

test:
	pytest backend/

lint:
	ruff check backend/
