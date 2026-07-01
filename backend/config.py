from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    alerte_seuil: int = 75
    environment: str = "development"
    secret_key: str = "demo-secret-key"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Intégration Microsoft Graph / Outlook (synchro des PDF Kizeo par email)
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    outlook_user_email: str = ""

    # Planificateur de synchronisation automatique (désactivé par défaut)
    sync_enabled: bool = False
    sync_interval_minutes: int = 15

    # Envoi des emails d'alerte (SMTP). Désactivé tant que non configuré.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True
    # Destinataires des alertes (séparés par des virgules dans le .env).
    alerte_destinataires: str = ""

    # Authentification (JWT)
    jwt_expire_minutes: int = 720  # 12 h
    # Compte administrateur créé au démarrage s'il n'existe aucun utilisateur.
    admin_username: str = "admin"
    admin_password: str = ""  # si vide, un mot de passe aléatoire est généré et journalisé

    @property
    def smtp_configure(self) -> bool:
        """Vrai si l'envoi d'emails d'alerte est configuré."""
        return bool(self.smtp_host and self.smtp_from and self.destinataires_alerte)

    @property
    def destinataires_alerte(self) -> list[str]:
        return [a.strip() for a in self.alerte_destinataires.split(",") if a.strip()]

    @property
    def sync_configure(self) -> bool:
        """Vrai si toutes les informations de connexion Graph sont présentes."""
        return bool(
            self.azure_tenant_id
            and self.azure_client_id
            and self.azure_client_secret
            and self.outlook_user_email
        )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
