from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agentic AI BGV System"
    database_url: str = "sqlite:///./bgv_demo.db"
    bgv_api_base_url: str = "http://127.0.0.1:8000"
    offer_acceptance_form_url: str = "https://forms.office.com/r/your-offer-acceptance-form"
    bgv_form_url: str = "https://forms.office.com/r/your-bgv-document-form"
    gmail_demo_mode: bool = True
    gmail_sender: str = "hr@example.com"
    openai_api_key: str = ""
    ms_tenant_id: str = ""
    ms_client_id: str = ""
    ms_client_secret: str = ""
    ms_sender_email: str = "hr@example.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
