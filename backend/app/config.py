from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Team Policy Assistant"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://policy_assistant:policy_assistant_dev@localhost:5432/policy_assistant"
    rabbitmq_url: str = "amqp://policy_assistant:policy_assistant_dev@localhost:5672/"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "team-policy"
    keycloak_client_id: str = "policy-web"
    keycloak_audience: str | None = None
    ai_provider: str = "none"
    ai_api_key: str | None = None
    upload_dir: str = "data/uploads"
    max_upload_bytes: int = 10_000_000
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else Path(__file__).resolve().parents[2] / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
