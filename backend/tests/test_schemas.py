"""Tests de la sérialisation UTC des dates (corrige le décalage de fuseau).

Les datetimes du backend sont stockés en UTC naïf. À la sortie JSON, ils doivent
porter le marqueur 'Z' pour que le navigateur les convertisse correctement en
heure locale.
"""
from datetime import datetime, timezone, timedelta

from backend.schemas import _to_utc_iso, BenneSchema


def test_to_utc_iso_naif_ajoute_z():
    dt = datetime(2026, 6, 22, 8, 4, 46)  # naïf, considéré UTC
    out = _to_utc_iso(dt)
    assert out.endswith("Z")
    assert out.startswith("2026-06-22T08:04:46")


def test_to_utc_iso_aware_converti_en_utc():
    # 10:04 en UTC+2 == 08:04 UTC
    cest = timezone(timedelta(hours=2))
    dt = datetime(2026, 6, 22, 10, 4, 46, tzinfo=cest)
    out = _to_utc_iso(dt)
    assert out.endswith("Z")
    assert out.startswith("2026-06-22T08:04:46")


def test_benne_schema_serialise_les_dates_en_z():
    benne = BenneSchema(
        id=1,
        type_dechet="Bois",
        taux=80,
        a_compacteur=False,
        tassee=True,
        tassee_at=datetime(2026, 6, 22, 8, 0, 0),
        tassement_prevu_at=None,
        rotation_prevue_at=None,
    )
    data = benne.model_dump(mode="json")
    assert data["tassee_at"].endswith("Z")
    assert data["rotation_prevue_at"] is None


def test_benne_schema_valeurs_par_defaut():
    benne = BenneSchema(id=1, type_dechet="Carton", taux=10, a_compacteur=False)
    assert benne.seuil_avertissement == 75
    assert benne.seuil_critique == 90
    assert benne.tassee is False
