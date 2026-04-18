from openai import AsyncOpenAI, OpenAI

from app.core.config import settings


def get_openai_client() -> OpenAI:
    """Create an OpenAI client from environment settings."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=settings.openai_api_key)


def get_async_openai_client() -> AsyncOpenAI:
    """Create an async OpenAI client from environment settings."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")
    return AsyncOpenAI(api_key=settings.openai_api_key)
