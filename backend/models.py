from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String, Timestamp, func
from sqlalchemy.orm import relationship
from backend.database import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    nom = Column(String(200), nullable=False)
    actif = Column(Boolean, default=True)
    created_at = Column(Timestamp, server_default=func.now())

    releves = relationship("Releve", back_populates="site")


class Releve(Base):
    __tablename__ = "releves"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    date_releve = Column(Date, nullable=False)
    agent = Column(String(200))
    email_message_id = Column(String(500), unique=True)
    recu_at = Column(Timestamp, server_default=func.now())

    site = relationship("Site", back_populates="releves")
    bennes = relationship("Benne", back_populates="releve", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_releves_site_date", "site_id", date_releve.desc()),
    )


class Benne(Base):
    __tablename__ = "bennes"

    id = Column(Integer, primary_key=True, index=True)
    releve_id = Column(Integer, ForeignKey("releves.id", ondelete="CASCADE"), nullable=False)
    type_dechet = Column(String(100), nullable=False)
    taux = Column(Integer, nullable=False)
    a_compacteur = Column(Boolean, default=False)

    releve = relationship("Releve", back_populates="bennes")
    alertes = relationship("Alerte", back_populates="benne")

    __table_args__ = (
        Index("idx_bennes_type", "type_dechet"),
    )


class Alerte(Base):
    __tablename__ = "alertes"

    id = Column(Integer, primary_key=True, index=True)
    benne_id = Column(Integer, ForeignKey("bennes.id"), nullable=False)
    seuil_declenche = Column(Integer, nullable=False)
    email_destinataire = Column(String(200))
    envoye_at = Column(Timestamp, server_default=func.now())
    statut = Column(String(50), default="envoye")

    benne = relationship("Benne", back_populates="alertes")

    __table_args__ = (
        Index("idx_alertes_benne", "benne_id"),
    )
