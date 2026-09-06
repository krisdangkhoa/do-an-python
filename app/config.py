from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/app.db"
    SECRET_KEY: str = "change-me"
    APP_NAME: str = "Quan ly thu chi ca nhan"


settings = Settings()
