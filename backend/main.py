import logging
import os
import secrets
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.routers import bennes, alertes, upload, parametrage, sync, auth, reporting
from backend.routers.auth import get_current_user
from backend.services.ingestion import run_sync_pipeline
from backend.security import hash_password
from backend import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _seed_admin():
    """Crée un compte administrateur initial si aucun utilisateur n'existe."""
    db = SessionLocal()
    try:
        if db.query(models.User).count() > 0:
            return
        pwd = settings.admin_password or secrets.token_urlsafe(12)
        db.add(models.User(
            username=settings.admin_username,
            hashed_password=hash_password(pwd),
            role="admin",
        ))
        db.commit()
        if settings.admin_password:
            logger.info(f"Compte administrateur initial créé : « {settings.admin_username} »")
        else:
            logger.warning(
                f"Compte administrateur initial créé : « {settings.admin_username} » / « {pwd} » "
                "— définissez ADMIN_PASSWORD et changez-le."
            )
    finally:
        db.close()


def _gerer_schema():
    """Crée le schéma puis aligne l'historique des migrations Alembic.

    - Base sans suivi Alembic (créée par create_all) : on complète le schéma via
      create_all puis on « stampe » la révision courante (aucune migration rejouée).
    - Base déjà suivie par Alembic : on applique les migrations en attente.

    Résultat : les bases existantes ne sont pas cassées, et les futures migrations
    s'appliqueront automatiquement au démarrage.
    """
    from alembic.config import Config
    from alembic import command
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import text

    Base.metadata.create_all(bind=engine)

    base_dir = os.path.dirname(__file__)
    cfg = Config(os.path.join(base_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(base_dir, "migrations"))

    # Révisions connues de nos scripts, et révision actuelle de la base.
    revisions_connues = {rev.revision for rev in ScriptDirectory.from_config(cfg).walk_revisions()}
    with engine.connect() as conn:
        revision_actuelle = MigrationContext.configure(conn).get_current_revision()

    if revision_actuelle in revisions_connues:
        # Base suivie par Alembic : on applique les migrations en attente.
        command.upgrade(cfg, "head")
        logger.info("Schéma : migrations Alembic en attente appliquées.")
    else:
        # Base sans suivi ou avec une révision orpheline (inconnue de nos scripts) :
        # create_all a déjà construit le schéma courant. On repart d'une table de
        # version propre, sinon Alembic ne sait pas résoudre la révision orpheline.
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        command.stamp(cfg, "head")
        logger.info(f"Schéma : base alignée sur head par stamp (révision précédente : {revision_actuelle}).")


async def _job_synchronisation():
    """Tâche périodique : exécute le pipeline de synchronisation Kizeo."""
    db = SessionLocal()
    try:
        stats = await run_sync_pipeline(db)
        logger.info(f"Synchronisation automatique terminée : {stats}")
    except Exception as e:
        logger.error(f"Synchronisation automatique en échec : {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _gerer_schema()
    _seed_admin()

    scheduler = None
    if settings.sync_enabled and settings.sync_configure:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _job_synchronisation, "interval",
            minutes=settings.sync_interval_minutes, id="kizeo_sync",
        )
        scheduler.start()
        logger.info(f"Planificateur de synchronisation actif (toutes les {settings.sync_interval_minutes} min)")
    elif settings.sync_enabled:
        logger.warning("SYNC_ENABLED=true mais configuration Azure/Outlook incomplète : planificateur non démarré.")

    yield

    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="SOTREMA — Suivi des bennes (démo)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentification : routes publiques (login). Les autres routers exigent un jeton valide.
app.include_router(auth.router)

_auth = [Depends(get_current_user)]
app.include_router(bennes.router, dependencies=_auth)
app.include_router(alertes.router, dependencies=_auth)
app.include_router(upload.router, dependencies=_auth)
app.include_router(parametrage.router, dependencies=_auth)
app.include_router(sync.router, dependencies=_auth)
app.include_router(reporting.router, dependencies=_auth)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.environment}
