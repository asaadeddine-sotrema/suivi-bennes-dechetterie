import logging
from sqlalchemy.orm import Session
from backend import models
from backend.config import settings
from backend.services.email import envoyer_email

logger = logging.getLogger(__name__)


def enregistrer_alerte(db: Session, benne: models.Benne, site: models.Site, seuil: int) -> models.Alerte | None:
    """Persiste une alerte si la benne franchit un nouvel épisode de dépassement.

    N'envoie PAS d'email : l'envoi est groupé par l'appelant (un seul mail pour
    tout le cycle). Retourne l'alerte créée, ou None si elle est ignorée.

    Le dédoublonnage porte sur la benne *logique* (site + type de déchet), pas sur
    l'`id` de la ligne `Benne` (recréée à chaque relevé). Tant que la benne reste
    au-dessus du seuil, on ne re-notifie pas ; une nouvelle alerte n'est possible
    qu'après un relevé repassé sous le seuil (benne vidée), qui clôt l'épisode.
    """
    derniere = (
        db.query(models.Alerte)
        .join(models.Benne, models.Benne.id == models.Alerte.benne_id)
        .join(models.Releve, models.Releve.id == models.Benne.releve_id)
        .filter(
            models.Releve.site_id == site.id,
            models.Benne.type_dechet == benne.type_dechet,
        )
        .order_by(models.Alerte.envoye_at.desc(), models.Alerte.id.desc())
        .first()
    )
    if derniere is not None:
        videe_depuis = (
            db.query(models.Benne.id)
            .join(models.Releve, models.Releve.id == models.Benne.releve_id)
            .filter(
                models.Releve.site_id == site.id,
                models.Benne.type_dechet == benne.type_dechet,
                models.Benne.taux < seuil,
                models.Releve.recu_at > derniere.envoye_at,
            )
            .first()
        )
        if videe_depuis is None:
            logger.info(
                f"Alerte ignorée (déjà notifiée, benne toujours pleine) : "
                f"{benne.type_dechet} · {site.nom}"
            )
            return None

    alerte = models.Alerte(
        benne_id=benne.id,
        seuil_declenche=benne.taux,
        statut="enregistre",
    )
    db.add(alerte)
    db.flush()
    logger.info(f"Alerte enregistrée : {benne.type_dechet} · {site.nom} ({benne.taux}%)")
    return alerte


def envoyer_alertes_groupees(db: Session, alertes: list[tuple[models.Alerte, str, str, int]]) -> None:
    """Envoie un email récapitulatif **par déchèterie** pour les bennes en dépassement.

    `alertes` : liste de (alerte, nom_site, type_dechet, taux). Les alertes sont
    regroupées par site : un seul email par déchèterie, listant tous ses flux
    concernés. Le statut de chaque alerte est mis à jour en conséquence.
    """
    destinataires = settings.destinataires_alerte
    if not alertes or not destinataires:
        return

    par_site: dict[str, list] = {}
    for item in alertes:
        par_site.setdefault(item[1], []).append(item)

    dest_str = ", ".join(destinataires)
    for nom_site, items in par_site.items():
        lignes = [
            f"  • {type_dechet} : {taux}%"
            for (_a, _s, type_dechet, taux) in sorted(items, key=lambda a: a[2])
        ]
        n = len(items)
        corps = (
            f"Déchetterie {nom_site} — {n} benne(s) ont dépassé leur seuil de remplissage :\n\n"
            + "\n".join(lignes)
            + "\n\nPensez à planifier un tassement ou une rotation."
        )
        sujet = f"{nom_site} : {n} benne(s) à traiter"
        envoye = envoyer_email(sujet=sujet, corps=corps, destinataires=destinataires)

        statut = "envoye" if envoye else "enregistre"
        for alerte, *_ in items:
            alerte.statut = statut
            alerte.email_destinataire = dest_str
        logger.info(f"Alertes {nom_site} : {n} benne(s) notifiée(s) en un email · envoye={envoye}")
