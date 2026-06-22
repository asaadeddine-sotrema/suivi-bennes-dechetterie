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

    # Authentification (JWT)
    jwt_expire_minutes: int = 720  # 12 h
    # Compte administrateur créé au démarrage s'il n'existe aucun utilisateur.
    admin_username: str = "admin"
    admin_password: str = ""  # si vide, un mot de passe aléatoire est généré et journalisé

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
