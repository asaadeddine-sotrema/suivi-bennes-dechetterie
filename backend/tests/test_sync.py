"""Tests des endpoints de synchronisation."""
from backend.config import settings


def test_status_initial(client):
    resp = client.get("/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["en_cours"] is False
    assert body["derniere_synchro"] is None
    assert body["stats"] is None


def test_manual_non_configure_renvoie_503(client, monkeypatch):
    # On force l'absence de configuration Azure/Outlook (indépendant de l'env réel).
    monkeypatch.setattr(settings, "azure_tenant_id", "")
    monkeypatch.setattr(settings, "azure_client_id", "")
    monkeypatch.setattr(settings, "azure_client_secret", "")
    monkeypatch.setattr(settings, "outlook_user_email", "")
    resp = client.post("/sync/manual")
    assert resp.status_code == 503
    assert "non configurée" in resp.json()["detail"]
