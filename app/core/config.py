from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="AI E-commerce Automation System")
    app_version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")
    debug: bool = Field(default=True, alias="APP_DEBUG")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_transcription_model: str = Field(default="gpt-4o-transcribe")
    openai_cleanup_model: str = Field(default="gpt-4o")
    openai_vision_model: str = Field(default="gpt-4o")
    openai_studio_planning_model: str = Field(default="gpt-4o")
    openai_studio_image_model: str = Field(default="gpt-image-1.5")
    openai_product_image_model: str = Field(default="gpt-image-1.5")
    wikipedia_api_base: str = Field(default="https://en.wikipedia.org")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
