DC = docker-compose
PROJECT = suivi-bennes-dechetterie

.PHONY: start stop restart build rebuild logs logs-backend logs-frontend \
        shell-backend shell-db db-reset status test

## Démarrage / arrêt
start:
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_backend" -q) 2>/dev/null || true
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_frontend" -q) 2>/dev/null || true
	$(DC) up -d

stop:
	$(DC) stop

restart:
	$(DC) stop
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_backend" -q) 2>/dev/null || true
	docker rm -f $$(docker ps -a --filter "name=$(PROJECT)_frontend" -q) 2>/dev/null || true
	$(DC) up -d

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

## Tests backend (SQLite en mémoire, exécutés dans le container)
## Le code backend n'étant pas monté en volume, on copie les tests puis on lance pytest.
test:
	docker exec $(PROJECT)_backend_1 rm -rf /app/backend/tests
	docker cp backend/tests $(PROJECT)_backend_1:/app/backend/tests
	docker cp backend/pytest.ini $(PROJECT)_backend_1:/app/backend/pytest.ini
	docker exec $(PROJECT)_backend_1 pip install -q pytest==8.2.0
	docker exec -w /app/backend -e PYTHONPATH=/app $(PROJECT)_backend_1 python -m pytest
