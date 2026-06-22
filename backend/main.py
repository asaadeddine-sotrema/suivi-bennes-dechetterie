import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base
from backend.routers import bennes, alertes, upload, parametrage

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


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


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.environment}
