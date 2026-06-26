"""Tests de l'effet d'une baisse de taux sur l'état tassement/rotation (ingestion)."""
from backend import models
from backend.services.ingestion import appliquer_baisse_taux


def _tassement(**kw):
    base = dict(
        site_id=1, type_dechet="Bois",
        tassement_demande=False, tassee=False, rotation_faite=False, taux_reference=80,
    )
    base.update(kw)
    return models.Tassement(**base)


def test_demande_tassement_devient_tassee_quand_taux_inferieur():
    t = _tassement(tassement_demande=True, taux_reference=80)
    assert appliquer_baisse_taux(t, 60) is True
    assert t.tassement_demande is False
    assert t.tassee is True
    assert t.tassee_at is not None
    assert t.taux_reference is None


def test_rotation_levee_quand_taux_inferieur():
    t = _tassement(rotation_faite=True, taux_reference=80)
    assert appliquer_baisse_taux(t, 60) is True
    assert t.rotation_faite is False
    assert t.taux_reference is None


def test_demande_tassement_conservee_quand_taux_non_baisse():
    t = _tassement(tassement_demande=True, taux_reference=80)
    # Taux identique : pas de confirmation, on garde la demande.
    assert appliquer_baisse_taux(t, 80) is False
    assert t.tassement_demande is True
    assert t.tassee is False
    # Taux supérieur : idem.
    assert appliquer_baisse_taux(t, 95) is False
    assert t.tassement_demande is True


def test_tassee_confirmee_reste_jusqu_a_rotation():
    # Une benne déjà "Tassée" (taux_reference effacé) ne bouge plus, même si le taux baisse.
    t = _tassement(tassee=True, taux_reference=None)
    assert appliquer_baisse_taux(t, 10) is False
    assert t.tassee is True


def test_aucune_reference_ne_change_rien():
    t = _tassement(tassement_demande=True, taux_reference=None)
    assert appliquer_baisse_taux(t, 10) is False
    assert t.tassement_demande is True


def test_tassement_absent():
    assert appliquer_baisse_taux(None, 10) is False
