"""Tests du module de prévision de saturation."""
from datetime import date, timedelta

from backend.services.prevision import regression_lineaire, prevoir_saturation


def test_regression_droite_parfaite():
    # y = 2x + 10
    xs = [0, 1, 2, 3]
    ys = [10, 12, 14, 16]
    pente, ordonnee, r2 = regression_lineaire(xs, ys)
    assert round(pente, 6) == 2.0
    assert round(ordonnee, 6) == 10.0
    assert round(r2, 6) == 1.0


def test_regression_moins_de_deux_points():
    assert regression_lineaire([0], [50]) is None


def test_saturation_prevue():
    # +10 pts/jour à partir de 50 → atteint 90 en 4 jours.
    j0 = date(2026, 6, 1)
    points = [(j0 + timedelta(days=i), 50 + 10 * i) for i in range(4)]  # 50,60,70,80
    p = prevoir_saturation("Bois", points, seuil_critique=90)
    assert p.statut == "saturation"
    assert p.pente == 10.0
    assert p.date_saturation == date(2026, 6, 5)  # jour 4
    assert p.jours_restants == 1  # dernier point au jour 3, seuil au jour 4


def test_tendance_stable_ou_baisse():
    j0 = date(2026, 6, 1)
    points = [(j0 + timedelta(days=i), 80 - 5 * i) for i in range(4)]  # en baisse
    p = prevoir_saturation("Carton", points, seuil_critique=90)
    assert p.statut == "stable"
    assert p.date_saturation is None
    assert p.jours_restants is None


def test_deja_saturee():
    j0 = date(2026, 6, 1)
    points = [(j0, 88), (j0 + timedelta(days=1), 95)]
    p = prevoir_saturation("Gravât", points, seuil_critique=90)
    assert p.statut == "deja_saturee"


def test_historique_insuffisant():
    p = prevoir_saturation("Ferraille", [(date(2026, 6, 1), 50)], seuil_critique=90)
    assert p.statut == "insuffisant"
    assert p.n_points == 1
