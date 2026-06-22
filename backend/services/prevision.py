"""Prévision de saturation des bennes par régression linéaire.

Approche volontairement simple et explicable : on ajuste une droite des moindres
carrés sur l'historique (jour → taux de remplissage) et on extrapole la date à
laquelle le seuil critique sera atteint. Avec peu de points, c'est une tendance
indicative, pas une prédiction de précision — d'où les indicateurs de fiabilité
(`n_points`, `r2`) renvoyés au client.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil


@dataclass
class Prevision:
    type_dechet: str
    taux_actuel: int
    pente: float                  # points de remplissage par jour
    r2: float                     # qualité de l'ajustement (0..1)
    n_points: int
    statut: str                   # 'saturation' | 'stable' | 'deja_saturee' | 'insuffisant'
    date_saturation: date | None = None
    jours_restants: int | None = None


def regression_lineaire(xs: list[float], ys: list[float]):
    """Droite des moindres carrés. Retourne (pente, ordonnee, r2) ou None."""
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:  # tous les relevés le même jour
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    pente = sxy / sxx
    ordonnee = my - pente * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (pente * x + ordonnee)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return pente, ordonnee, r2


def prevoir_saturation(type_dechet: str, points: list[tuple[date, int]], seuil_critique: int) -> Prevision:
    """Estime la date d'atteinte du seuil critique à partir de (date, taux)."""
    points = sorted(points, key=lambda p: p[0])
    taux_actuel = points[-1][1] if points else 0

    if len(points) < 2:
        return Prevision(type_dechet, taux_actuel, 0.0, 0.0, len(points), "insuffisant")

    jour0 = points[0][0]
    xs = [(d - jour0).days for d, _ in points]
    ys = [float(t) for _, t in points]

    reg = regression_lineaire(xs, ys)
    if reg is None:
        return Prevision(type_dechet, taux_actuel, 0.0, 0.0, len(points), "insuffisant")
    pente, ordonnee, r2 = reg

    if taux_actuel >= seuil_critique:
        return Prevision(type_dechet, taux_actuel, round(pente, 2), round(r2, 3), len(points), "deja_saturee")

    if pente <= 0:  # stable ou en baisse : pas de saturation prévisible
        return Prevision(type_dechet, taux_actuel, round(pente, 2), round(r2, 3), len(points), "stable")

    jour_seuil = (seuil_critique - ordonnee) / pente
    jours_restants = max(0, ceil(jour_seuil - xs[-1]))
    date_saturation = jour0 + timedelta(days=int(round(jour_seuil)))
    return Prevision(
        type_dechet, taux_actuel, round(pente, 2), round(r2, 3), len(points),
        "saturation", date_saturation, jours_restants,
    )
