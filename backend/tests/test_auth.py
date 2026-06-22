"""Tests de l'authentification et des rôles."""
from types import SimpleNamespace

import pytest

from backend.main import app
from backend.routers.auth import get_current_user, require_admin
from backend.security import hash_password, verify_password
from backend import models


def test_hash_password_roundtrip():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h)
    assert not verify_password("mauvais", h)


@pytest.fixture
def sans_auth():
    """Retire temporairement la surcharge d'authentification (comportement réel)."""
    saved = app.dependency_overrides.pop(get_current_user, None)
    yield
    if saved:
        app.dependency_overrides[get_current_user] = saved


def _creer_user(db, username, password, role="operateur"):
    u = models.User(username=username, hashed_password=hash_password(password), role=role)
    db.add(u)
    db.commit()
    return u


def test_acces_protege_sans_jeton(client, sans_auth):
    assert client.get("/bennes/").status_code == 401


def test_login_et_me(client, db, sans_auth):
    _creer_user(db, "agent", "motdepasse", role="operateur")
    resp = client.post("/auth/login", json={"username": "agent", "password": "motdepasse"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["role"] == "operateur"
    token = body["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "agent"


def test_login_mauvais_mot_de_passe(client, db, sans_auth):
    _creer_user(db, "agent", "motdepasse")
    resp = client.post("/auth/login", json={"username": "agent", "password": "faux"})
    assert resp.status_code == 401


@pytest.fixture
def as_operateur():
    """Force l'utilisateur courant à être un opérateur (non admin)."""
    op = SimpleNamespace(id=2, username="op", role="operateur", actif=True)
    app.dependency_overrides[get_current_user] = lambda: op
    yield
    from backend.tests.conftest import ADMIN
    app.dependency_overrides[get_current_user] = lambda: ADMIN


def test_operateur_interdit_sur_route_admin(client, as_operateur):
    # Modifier un seuil est réservé aux admins.
    resp = client.put("/parametrage/seuils/1/Bois", json={"seuil_avertissement": 60, "seuil_critique": 85})
    assert resp.status_code == 403


def test_operateur_autorise_en_lecture(client, as_operateur):
    assert client.get("/bennes/").status_code == 200
