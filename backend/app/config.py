from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

# libpq spells SSL options as query parameters; asyncpg takes them as `connect()`
# arguments instead. Map the common values and drop params asyncpg rejects.
_SSL_MODE_ALIASES = {
    "true": "require",
    "1": "require",
    "require": "require",
    "verify-ca": "verify-ca",
    "verify-full": "verify-full",
    "prefer": "prefer",
    "allow": "allow",
    "disable": "disable",
    "false": "disable",
    "0": "disable",
}

_UNSUPPORTED_ASYNCPG_PARAMS = {"channel_binding"}


def _normalize_database_url(url: str) -> tuple[str, str | None]:
    """Return an asyncpg-compatible URL plus the SSL mode, if one was requested."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if not url.startswith("postgresql+asyncpg://"):
        return url, None

    parts = urlsplit(url)
    ssl_mode: str | None = None
    kept_params: list[tuple[str, str]] = []

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key in {"sslmode", "ssl"}:
            ssl_mode = _SSL_MODE_ALIASES.get(value.lower(), value.lower())
        elif key in _UNSUPPORTED_ASYNCPG_PARAMS:
            continue
        else:
            kept_params.append((key, value))

    cleaned = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(kept_params), parts.fragment)
    )
    return cleaned, ssl_mode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DevFlow"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite+aiosqlite:///./devflow.db"
    sql_echo: bool = False

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    groq_api_key: str = ""
    llm_model: str = "groq/llama-3.3-70b-versatile"

    @property
    def database_url_async(self) -> str:
        return _normalize_database_url(self.database_url)[0]

    @property
    def database_ssl_mode(self) -> str | None:
        return _normalize_database_url(self.database_url)[1]

    @property
    def database_connect_args(self) -> dict[str, str]:
        if self.database_url_async.startswith("postgresql+asyncpg") and self.database_ssl_mode:
            return {"ssl": self.database_ssl_mode}
        return {}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.groq_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
