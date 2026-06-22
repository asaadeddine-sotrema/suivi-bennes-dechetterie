import logging
import secrets
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.routers import bennes, alertes, upload, parametrage, sync, auth
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
    Base.metadata.create_all(bind=engine)
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


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.environment}
