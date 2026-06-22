from datetime import date, datetime
from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import relationship
from backend.database import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    nom = Column(String(200), nullable=False)
    actif = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    releves = relationship("Releve", back_populates="site")


class Releve(Base):
    __tablename__ = "releves"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    date_releve = Column(Date, nullable=False)
    agent = Column(String(200))
    email_message_id = Column(String(500), unique=True)
    recu_at = Column(TIMESTAMP, server_default=func.now())

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


class Tassement(Base):
    __tablename__ = "tassements"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    type_dechet = Column(String(100), nullable=False)
    tassee = Column(Boolean, default=False, nullable=False)
    tassee_at = Column(TIMESTAMP, nullable=True)
    tassement_prevu_at = Column(TIMESTAMP, nullable=True)
    rotation_prevue_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        UniqueConstraint("site_id", "type_dechet", name="uq_tassement_site_type"),
    )


class HistoriqueTassement(Base):
    __tablename__ = "historique_tassements"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    type_dechet = Column(String(100), nullable=False)
    evenement = Column(String(20), nullable=False)  # 'tassement' ou 'rotation'
    fait_le = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_historique_site_type", "site_id", "type_dechet"),
    )


class SeuilAlerte(Base):
    __tablename__ = "seuils_alertes"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    type_dechet = Column(String(100), nullable=False)
    seuil_avertissement = Column(Integer, default=75, nullable=False)
    seuil_critique = Column(Integer, default=90, nullable=False)

    __table_args__ = (
        UniqueConstraint("site_id", "type_dechet", name="uq_seuil_site_type"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="operateur", nullable=False)  # 'admin' ou 'operateur'
    actif = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Alerte(Base):
    __tablename__ = "alertes"

    id = Column(Integer, primary_key=True, index=True)
    benne_id = Column(Integer, ForeignKey("bennes.id"), nullable=False)
    seuil_declenche = Column(Integer, nullable=False)
    email_destinataire = Column(String(200))
    envoye_at = Column(TIMESTAMP, server_default=func.now())
    statut = Column(String(50), default="envoye")

    benne = relationship("Benne", back_populates="alertes")

    __table_args__ = (
        Index("idx_alertes_benne", "benne_id"),
    )
