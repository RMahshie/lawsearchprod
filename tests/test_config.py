from app.core.config import Settings


def test_database_url_uses_psycopg_driver_for_railway_postgres_url():
    settings = Settings(
        _env_file=None,
        openai_api_key="test-key",
        database_url="postgresql://user:pass@host:5432/db",
    )

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_database_url_accepts_legacy_postgres_scheme():
    settings = Settings(
        _env_file=None,
        openai_api_key="test-key",
        database_url="postgres://user:pass@host:5432/db",
    )

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_cors_origins_accept_comma_separated_env_style_value():
    settings = Settings(
        _env_file=None,
        openai_api_key="test-key",
        cors_origins="https://frontend.up.railway.app, https://custom.example",
    )

    assert settings.cors_origins == [
        "https://frontend.up.railway.app",
        "https://custom.example",
    ]


def test_cors_origins_accept_comma_separated_environment_value(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://frontend.up.railway.app, https://custom.example",
    )

    settings = Settings(_env_file=None, openai_api_key="test-key")

    assert settings.cors_origins == [
        "https://frontend.up.railway.app",
        "https://custom.example",
    ]
