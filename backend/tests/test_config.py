from pathlib import Path

import pytest

from app.config import load_settings

ENVIRONMENT_VARIABLES = (
    "PROVIDER_TIMEOUT_SECONDS",
    "MAX_CONCURRENCY",
    "PROVIDER_BASE_URL",
    "FRONTEND_ORIGIN",
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
            )
        ),
        encoding="utf-8",
    )

    settings = load_settings(env_file)

    assert settings.provider_timeout_seconds == 2.5
    assert settings.max_concurrency == 4
    assert settings.provider_base_url == "https://provider.test"
    assert settings.frontend_origin == "https://frontend.test"


def test_process_environment_overrides_backend_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_environment(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("MAX_CONCURRENCY=4", encoding="utf-8")
    monkeypatch.setenv("MAX_CONCURRENCY", "8")

    settings = load_settings(env_file)

    assert settings.max_concurrency == 8
