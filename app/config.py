from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/app.db"
    SECRET_KEY: str = "change-me"
    APP_NAME: str = "Quan ly thu chi ca nhan"

    # Gui email. De trong thi chay che do thu: in noi dung ra man hinh.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = ""

    # Email gan cho tai khoan khoa khi chay seed_data.py
    DEMO_EMAIL: str = ""


settings = Settings()