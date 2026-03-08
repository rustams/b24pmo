.PHONY: help dev-init create-version delete-version dev-front dev-python prod-python status ps down down-all logs clean queue-up queue-down security-scan security-tests db-backup db-restore

DOCKER_COMPOSE = docker compose

.DEFAULT_GOAL := help

help:
	@echo "🚀 PMO Hub (Bitrix24 Starter) - Commands"
	@echo ""
	@echo "Setup:"
	@echo "  dev-init        Interactive project setup"
	@echo "  create-version  Clone current project into versions/<name>"
	@echo "  delete-version  Remove versions/<name>"
	@echo ""
	@echo "Development:"
	@echo "  dev-front       Start frontend only"
	@echo "  dev-python      Start frontend + python backend (+db, +queue if enabled)"
	@echo ""
	@echo "Production:"
	@echo "  prod-python     Start python profile in production mode"
	@echo ""
	@echo "Operations:"
	@echo "  logs            Follow logs"
	@echo "  down            Stop all local services"
	@echo "  clean           Docker cleanup"
	@echo "  queue-up        Start RabbitMQ only"
	@echo "  queue-down      Stop RabbitMQ only"
	@echo ""
	@echo "Security:"
	@echo "  security-scan   Dependency vulnerability audit"
	@echo "  security-tests  Orchestrated security test suite"

dev-init:
	@./scripts/dev-init.sh

create-version:
	@./scripts/create-version.sh $(VERSION)

delete-version:
	@./scripts/delete-version.sh $(VERSION)

dev-front:
	COMPOSE_PROFILES=frontend,cloudpub docker compose --env-file .env up --build

dev-python:
	@DB_TYPE_VALUE=$$(grep -E '^DB_TYPE=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
	if [ -z "$$DB_TYPE_VALUE" ]; then DB_TYPE_VALUE=postgresql; fi; \
	if [ "$$DB_TYPE_VALUE" = "mysql" ]; then DB_PROFILE="db-mysql"; else DB_PROFILE="db-postgres"; fi; \
	ENABLE_RABBITMQ_VALUE=$$(grep -E '^ENABLE_RABBITMQ=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
	if [ -z "$$ENABLE_RABBITMQ_VALUE" ]; then ENABLE_RABBITMQ_VALUE=0; fi; \
	if [ "$$ENABLE_RABBITMQ_VALUE" = "1" ]; then \
	  PROFILES="frontend,python,cloudpub,queue,$$DB_PROFILE"; \
	else \
	  PROFILES="frontend,python,cloudpub,$$DB_PROFILE"; \
	fi; \
	COMPOSE_PROFILES=$$PROFILES docker compose --env-file .env up --build

prod-python:
	COMPOSE_PROFILES=python FRONTEND_TARGET=production docker compose up --build -d

security-scan:
	@./scripts/security-scan.sh

security-tests:
	@./scripts/security-tests.sh $(SECURITY_TESTS_ARGS)

status:
	docker stats

ps:
	watch -n 2 docker ps

down:
	COMPOSE_PROFILES=frontend,python,cloudpub,queue,db-postgres,db-mysql docker compose down --remove-orphans || true

down-all:
	docker compose down --remove-orphans

queue-up:
	@ENABLE_RABBITMQ_VALUE=$$(grep -E '^ENABLE_RABBITMQ=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
	if [ -z "$$ENABLE_RABBITMQ_VALUE" ]; then ENABLE_RABBITMQ_VALUE=0; fi; \
	if [ "$$ENABLE_RABBITMQ_VALUE" != "1" ]; then \
	  echo "⚠ ENABLE_RABBITMQ=0 в .env — проверьте конфигурацию"; \
	fi; \
	COMPOSE_PROFILES=queue docker compose --env-file .env up rabbitmq --build -d

queue-down:
	COMPOSE_PROFILES=queue docker compose --env-file .env stop rabbitmq || true

clean:
	docker compose down --remove-orphans --volumes || true
	docker network prune -f
	docker volume prune -f

logs:
	docker compose logs -f

db-backup:
	@DB_TYPE_VALUE=$$(grep -E '^DB_TYPE=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
	if [ -z "$$DB_TYPE_VALUE" ]; then DB_TYPE_VALUE=postgresql; fi; \
	if [ "$$DB_TYPE_VALUE" = "mysql" ]; then \
	  COMPOSE_PROFILES=db-mysql docker compose exec -T database-mysql sh -lc "exec mysqldump -u\"$${DB_USER:-appuser}\" -p\"$${DB_PASSWORD:-apppass}\" \"$${DB_NAME:-appdb}\"" > backup_$(shell date +%Y%m%d_%H%M%S).sql; \
	else \
	  COMPOSE_PROFILES=db-postgres docker compose exec -T database-postgres pg_dump -U $${DB_USER:-appuser} $${DB_NAME:-appdb} > backup_$(shell date +%Y%m%d_%H%M%S).sql; \
	fi

db-restore:
	@DB_TYPE_VALUE=$$(grep -E '^DB_TYPE=' .env 2>/dev/null | tail -n1 | cut -d= -f2); \
	if [ -z "$$DB_TYPE_VALUE" ]; then DB_TYPE_VALUE=postgresql; fi; \
	if [ "$$DB_TYPE_VALUE" = "mysql" ]; then \
	  COMPOSE_PROFILES=db-mysql docker compose exec -T database-mysql sh -lc "exec mysql -u\"$${DB_USER:-appuser}\" -p\"$${DB_PASSWORD:-apppass}\" \"$${DB_NAME:-appdb}\"" < $(file); \
	else \
	  COMPOSE_PROFILES=db-postgres docker compose exec -T database-postgres psql -U $${DB_USER:-appuser} $${DB_NAME:-appdb} < $(file); \
	fi
