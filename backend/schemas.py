from datetime import date, datetime
from pydantic import BaseModel


class BenneSchema(BaseModel):
    id: int
    type_dechet: str
    taux: int
    a_compacteur: bool
    tassee: bool = False
    tassee_at: datetime | None = None
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
    fait_le: datetime

    class Config:
        from_attributes = True


class TypeDechetPayload(BaseModel):
    type_dechet: str


class TassementPayload(BaseModel):
    type_dechet: str
    tassee: bool


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
