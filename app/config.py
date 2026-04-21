# app/config.py
from dataclasses import dataclass # For defining the Settings data class - a convenient way to store configuration settings.
from functools import lru_cache  # For caching the settings instance - load settings only 1 time..
from pathlib import Path # For handling file paths - used for the chroma_persist_dir setting.
import os

from dotenv import load_dotenv


@dataclass(frozen=True) # Define the Settings data class to hold all configuration settings. The frozen=True parameter makes it immutable.
class Settings:
    openai_api_key: str
    openai_chat_model: str
    openai_embedding_model: str
    sql_server_connection_string: str
    chroma_persist_dir: Path


@lru_cache(maxsize=1) # Cache the settings instance to ensure it's only loaded once. Subsequent calls will return the cached instance.
def get_settings() -> Settings:
    load_dotenv()

    # Load values from the local .env file into process environment variables.
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    sql_server_connection_string = os.getenv("SQL_SERVER_CONNECTION_STRING", "").strip()
    if not sql_server_connection_string:
        raise RuntimeError("SQL_SERVER_CONNECTION_STRING is missing")

    # Keep the values in one place so the rest of the app can reuse them.
    return Settings(
        openai_api_key=openai_api_key,
        openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip(),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip(),
        sql_server_connection_string=sql_server_connection_string,
        # Resolve the Chroma folder once so later code can use an absolute path.
        chroma_persist_dir=Path(os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")).resolve(),
    )