"""Environment-driven settings. Secrets come from env / .env, never from source."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FitQuest API"
    ENV: str = "dev"
    CORS_ORIGINS: str = "*"

    DATABASE_URL: str = "postgresql+psycopg2://fitquest:fitquest@db:5432/fitquest"

    SECRET_KEY: str = "CHANGE_ME_dev_only_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    TELEMETRY_WS_INTERVAL_SECONDS: float = 5.0
    MOCK_WEBHOOK_SECRET: str = "dev-mock-webhook-secret"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
