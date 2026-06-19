from datetime import date, datetime
from pydantic import BaseModel


class BenneSchema(BaseModel):
    id: int
    type_dechet: str
    taux: int
    a_compacteur: bool

    class Config:
        from_attributes = True


class ReleveSchema(BaseModel):
    id: int
    date_releve: date
    agent: str | None
    recu_at: datetime | None

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
    envoye_at: datetime | None
    statut: str

    class Config:
        from_attributes = True


class SyncStats(BaseModel):
    traites: int
    ignores: int
    erreurs: int
    alertes: int


class SyncStatus(BaseModel):
    derniere_synchro: datetime | None
    stats: SyncStats | None
    en_cours: bool
