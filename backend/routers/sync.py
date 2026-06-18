import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, SessionLocal
from backend.services.ingestion import run_sync_pipeline
from backend import schemas

router = APIRouter(prefix="/sync", tags=["sync"])
logger = logging.getLogger(__name__)

_last_sync_stats: dict | None = None
_last_sync_time: datetime | None = None
_sync_en_cours: bool = False


@router.post("/manual", response_model=schemas.SyncStats)
async def sync_manual(db: Session = Depends(get_db)):
    """Déclenche une synchronisation manuelle immédiate."""
    global _last_sync_stats, _last_sync_time, _sync_en_cours

    if _sync_en_cours:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Une synchronisation est déjà en cours")

    _sync_en_cours = True
    try:
        stats = await run_sync_pipeline(db)
        _last_sync_stats = stats
        _last_sync_time = datetime.utcnow()
        return stats
    finally:
        _sync_en_cours = False


@router.get("/status", response_model=schemas.SyncStatus)
def get_sync_status():
    """Retourne le statut de la dernière synchronisation."""
    return schemas.SyncStatus(
        derniere_synchro=_last_sync_time,
        stats=schemas.SyncStats(**_last_sync_stats) if _last_sync_stats else None,
        en_cours=_sync_en_cours,
    )
