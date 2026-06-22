from datetime import date, datetime, timezone
from typing import Annotated
from pydantic import BaseModel, PlainSerializer


def _to_utc_iso(dt: datetime) -> str:
    """Sérialise un datetime en ISO 8601 UTC avec suffixe 'Z'.

    Les datetimes du backend sont stockés en UTC naïf (datetime.utcnow()).
    Sans marqueur de fuseau, le navigateur les interprète comme heure locale,
    d'où un décalage. On force donc l'UTC explicite côté sortie JSON.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


UTCDateTime = Annotated[datetime, PlainSerializer(_to_utc_iso, return_type=str, when_used="json")]


class BenneSchema(BaseModel):
    id: int
    type_dechet: str
    taux: int
    a_compacteur: bool
    tassee: bool = False
    tassee_at: UTCDateTime | None = None
    tassement_prevu_at: UTCDateTime | None = None
    rotation_prevue_at: UTCDateTime | None = None
    seuil_avertissement: int = 75
    seuil_critique: int = 90

    class Config:
        from_attributes = True


class SeuilAlerteSchema(BaseModel):
    site_id: int
    site_nom: str
    type_dechet: str
    seuil_avertissement: int
    seuil_critique: int


class SeuilAlerteUpdate(BaseModel):
    seuil_avertissement: int
    seuil_critique: int


class EvenementTassement(BaseModel):
    id: int
    evenement: str
    fait_le: UTCDateTime

    class Config:
        from_attributes = True


class TypeDechetPayload(BaseModel):
    type_dechet: str


class TassementPayload(BaseModel):
    type_dechet: str
    tassee: bool


class PlanifierTassementPayload(BaseModel):
    prevu_at: datetime


class ReleveSchema(BaseModel):
    id: int
    date_releve: date
    agent: str | None
    recu_at: UTCDateTime | None

    class Config:
        from_attributes = True


class ReleveDetail(ReleveSchema):
    bennes: list[BenneSchema] = []


class SiteSchema(BaseModel):
    id: int
    code: str
    nom: str
    actif: bool

    class Config:
        from_attributes = True


class SiteAvecDerniereReleve(BaseModel):
    site: SiteSchema
    releve: ReleveDetail | None

    class Config:
        from_attributes = True


class AlerteSchema(BaseModel):
    id: int
    benne_id: int
    type_dechet: str | None = None
    site_nom: str | None = None
    seuil_declenche: int
    email_destinataire: str | None
    envoye_at: UTCDateTime | None
    statut: str

    class Config:
        from_attributes = True


class SyncStats(BaseModel):
    traites: int
    ignores: int
    erreurs: int
    alertes: int


class SyncStatus(BaseModel):
    derniere_synchro: UTCDateTime | None
    stats: SyncStats | None
    en_cours: bool
