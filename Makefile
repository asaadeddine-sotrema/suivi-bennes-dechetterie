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
## Workaround pour le bug ContainerConfig de docker-compose 1.29.2
rebuild:
	$(DC) stop
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)" -q) 2>/dev/null || true
	$(DC) build --no-cache
	docker run -d --name $(PROJECT)_backend_1 --network $(PROJECT)_default \
	  --env-file .env -p 8000:8000 --restart unless-stopped \
	  $(PROJECT)_backend uvicorn backend.main:app --host 0.0.0.0 --port 8000
	docker run -d --name $(PROJECT)_frontend_1 --network $(PROJECT)_default \
	  -p 3000:80 --restart unless-stopped $(PROJECT)_frontend

rebuild-backend:
	$(DC) stop backend
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_backend" -q) 2>/dev/null || true
	$(DC) build --no-cache backend
	docker run -d --name $(PROJECT)_backend_1 --network $(PROJECT)_default \
	  --env-file .env -p 8000:8000 --restart unless-stopped \
	  $(PROJECT)_backend uvicorn backend.main:app --host 0.0.0.0 --port 8000

rebuild-frontend:
	$(DC) stop frontend
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_frontend" -q) 2>/dev/null || true
	$(DC) build --no-cache frontend
	docker run -d --name $(PROJECT)_frontend_1 --network $(PROJECT)_default \
	  -p 3000:80 --restart unless-stopped $(PROJECT)_frontend

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
