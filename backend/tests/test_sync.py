"""Tests des endpoints de synchronisation."""


def test_status_initial(client):
    resp = client.get("/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["en_cours"] is False
    assert body["derniere_synchro"] is None
    assert body["stats"] is None


def test_manual_non_configure_renvoie_503(client):
    # En environnement de test, aucune information Azure/Outlook n'est fournie.
    resp = client.post("/sync/manual")
    assert resp.status_code == 503
    assert "non configurée" in resp.json()["detail"]
