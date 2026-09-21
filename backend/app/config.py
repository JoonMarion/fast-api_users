import os
from dataclasses import dataclass
from pathlib import Path

MAX_USER_IDS = 100
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        name, separator, value = line.partition("=")
        name = name.strip()
        if not separator or not name:
            raise ValueError(f"Invalid environment entry at {path}:{line_number}")

        values[name] = value.strip()

    return values


def _get_setting(name: str, default: str, env_file_values: dict[str, str]) -> str:
    return os.getenv(name, env_file_values.get(name, default))


def _positive_float(name: str, raw_value: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _positive_int(name: str, raw_value: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    provider_timeout_seconds: float
    max_concurrency: int
    provider_base_url: str
    frontend_origin: str


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    env_file_values = _read_env_file(env_file)

    return Settings(
        provider_timeout_seconds=_positive_float(
            "PROVIDER_TIMEOUT_SECONDS",
            _get_setting("PROVIDER_TIMEOUT_SECONDS", "5", env_file_values),
        ),
        max_concurrency=_positive_int(
            "MAX_CONCURRENCY",
            _get_setting("MAX_CONCURRENCY", "10", env_file_values),
        ),
        provider_base_url=_get_setting(
            "PROVIDER_BASE_URL",
            "https://jsonplaceholder.typicode.com",
            env_file_values,
        ),
        frontend_origin=_get_setting(
            "FRONTEND_ORIGIN", "http://localhost:5173", env_file_values
        ),
    )
