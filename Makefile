DC = docker-compose
PROJECT = suivi-bennes-dechetterie

.PHONY: start stop restart build rebuild logs logs-backend logs-frontend \
        shell-backend shell-db db-reset status

## Démarrage / arrêt
start:
	$(DC) up -d

stop:
	$(DC) stop

restart:
	$(DC) stop
	$(DC) start

## Construction (sans recréer depuis zéro)
build:
	$(DC) build

## Reconstruction complète (supprime les containers puis rebuild)
rebuild:
	$(DC) stop
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)" -q) 2>/dev/null || true
	$(DC) build --no-cache
	$(DC) up -d

## Reconstruction d'un seul service : make rebuild-backend  ou  make rebuild-frontend
rebuild-backend:
	$(DC) stop backend
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_backend" -q) 2>/dev/null || true
	$(DC) build --no-cache backend
	$(DC) up -d backend

rebuild-frontend:
	$(DC) stop frontend
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_frontend" -q) 2>/dev/null || true
	$(DC) build --no-cache frontend
	$(DC) up -d frontend

## Logs
logs:
	$(DC) logs -f

logs-backend:
	$(DC) logs -f backend

logs-frontend:
	$(DC) logs -f frontend

## Shells interactifs
shell-backend:
	$(DC) exec backend bash

shell-db:
	$(DC) exec postgres psql -U sotrema -d sotrema_bennes

## Vider la base (garde la structure, efface les données)
db-reset:
	$(DC) exec postgres psql -U sotrema -d sotrema_bennes -c \
	  "TRUNCATE alertes, bennes, releves, sites RESTART IDENTITY CASCADE;"

## État des containers
status:
	$(DC) ps
