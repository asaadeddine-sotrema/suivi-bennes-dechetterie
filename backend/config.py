from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    alerte_seuil: int = 75
    environment: str = "development"
    secret_key: str = "demo-secret-key"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
