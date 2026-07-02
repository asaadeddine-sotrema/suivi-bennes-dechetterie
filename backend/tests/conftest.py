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

from types import SimpleNamespace

from backend.database import Base, get_db
from backend.main import app
from backend.routers.auth import get_current_user
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

# Par défaut, les tests s'exécutent en tant qu'administrateur authentifié.
# Les tests d'authentification/rôles ajustent ou retirent cette surcharge.
ADMIN = SimpleNamespace(id=1, username="test-admin", role="admin", actif=True)
app.dependency_overrides[get_current_user] = lambda: ADMIN


@pytest.fixture(autouse=True)
def reset_db():
    """Recrée un schéma vierge avant chaque test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _empeche_envoi_reel(monkeypatch):
    """Filet de sécurité : aucun test ne doit envoyer d'email réel.

    `make test` s'exécute dans le conteneur de prod (Azure/Graph configuré) ; sans
    ce garde-fou, tout test déclenchant une alerte enverrait un vrai mail via Graph.
    On neutralise les transports → `envoyer_email` devient un no-op.
    """
    from backend.config import settings
    for attr in (
        "azure_tenant_id", "azure_client_id", "azure_client_secret",
        "outlook_user_email", "smtp_host",
    ):
        monkeypatch.setattr(settings, attr, "")


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
