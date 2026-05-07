.PHONY: help up down restart logs logs-all migrate test ps shell

help:
	@echo ""
	@echo "Amazon Deals Bot — available commands:"
	@echo ""
	@echo "  make up        Start all services (detached)"
	@echo "  make down      Stop all services"
	@echo "  make restart   Restart the app container"
	@echo "  make logs      Follow app container logs"
	@echo "  make logs-all  Follow all service logs"
	@echo "  make migrate   Run Alembic database migrations"
	@echo "  make test      Run test suite"
	@echo "  make ps        Show service status"
	@echo "  make shell     Open bash shell inside app container"
	@echo ""

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart app

logs:
	docker compose logs -f app

logs-all:
	docker compose logs -f

migrate:
	docker compose exec app alembic upgrade head

test:
	docker compose exec app pytest tests/ -v

ps:
	docker compose ps

shell:
	docker compose exec app bash