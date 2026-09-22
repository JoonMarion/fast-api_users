from pathlib import Path

import pytest
from app.config import load_settings

ENVIRONMENT_VARIABLES = (
    "PROVIDER_TIMEOUT_SECONDS",
    "MAX_CONCURRENCY",
    "PROVIDER_BASE_URL",
    "FRONTEND_ORIGIN",
    "REDIS_URL",
    "CACHE_TTL_SECONDS",
    "CACHE_TIMEOUT_SECONDS",
)


def clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_load_settings_reads_backend_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            (
                "PROVIDER_TIMEOUT_SECONDS=2.5",
                "MAX_CONCURRENCY=4",
                "PROVIDER_BASE_URL=https://provider.test",
                "FRONTEND_ORIGIN=https://frontend.test",
                "REDIS_URL=redis://redis.test:6379/1",
                "CACHE_TTL_SECONDS=120",
                "CACHE_TIMEOUT_SECONDS=0.2",
            )
        ),
        encoding="utf-8",
    )

    settings = load_settings(env_file)

    assert settings.provider_timeout_seconds == 2.5
    assert settings.max_concurrency == 4
    assert settings.provider_base_url == "https://provider.test"
    assert settings.frontend_origin == "https://frontend.test"
    assert settings.redis_url == "redis://redis.test:6379/1"
    assert settings.cache_ttl_seconds == 120
    assert settings.cache_timeout_seconds == 0.2


def test_process_environment_overrides_backend_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("MAX_CONCURRENCY=4", encoding="utf-8")
    monkeypatch.setenv("MAX_CONCURRENCY", "8")

    settings = load_settings(env_file)

    assert settings.max_concurrency == 8


def test_load_settings_uses_cache_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_environment(monkeypatch)

    settings = load_settings(tmp_path / "missing.env")

    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.cache_ttl_seconds == 300
    assert settings.cache_timeout_seconds == 0.5
