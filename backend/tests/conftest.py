"""Configuration commune des tests.

On utilise une base SQLite en mémoire (isolée, rapide) et on remplace la
dépendance `get_db` de l'application. La base est réinitialisée avant chaque
test pour garantir l'isolation.
"""
import os

# Doit être défini avant l'import des modules backend (Settings exige DATABASE_URL).
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend import models  # noqa: F401  (enregistre les tables sur Base)

# Une seule connexion partagée pour toute la session (in-memory).
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Recrée un schéma vierge avant chaque test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    """Session directe pour préparer/inspecter les données dans un test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    # Sans context manager : le lifespan (create_all sur Postgres) n'est pas déclenché.
    return TestClient(app)
