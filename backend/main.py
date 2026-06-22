import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base, SessionLocal
from backend.routers import bennes, alertes, upload, parametrage, sync
from backend.services.ingestion import run_sync_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

app.include_router(bennes.router)
app.include_router(alertes.router)
app.include_router(upload.router)
app.include_router(parametrage.router)
app.include_router(sync.router)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.environment}
