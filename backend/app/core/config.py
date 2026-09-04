"""
Централизованная конфигурация приложения.
Все значения читаются из переменных окружения (см. .env.example в корне репозитория).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Общие
    APP_NAME: str = "FitQuest API"
    ENV: str = "dev"
    CORS_ORIGINS: str = "http://localhost:5173"

    # База данных
    DATABASE_URL: str = "postgresql+psycopg2://fitquest:fitquest@db:5432/fitquest"

    # JWT
    SECRET_KEY: str = "CHANGE_ME_dev_only_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 день, для учебного проекта норм

    # Stripe (тестовый режим!)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:5173/payments?status=success"
    STRIPE_CANCEL_URL: str = "http://localhost:5173/payments?status=cancel"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
