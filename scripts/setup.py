from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DEFAULT_PROVIDER_BASE_URL = "https://jsonplaceholder.typicode.com"
MINIMUM_PYTHON = (3, 11)


class SetupError(RuntimeError):
    """Raised when a requirement or setup step fails."""


def run(command: list[str], *, cwd: Path | None = None) -> None:
    display_command = " ".join(command)
    print(f"\n> {display_command}")

    try:
        subprocess.run(command, cwd=cwd, check=True)
    except subprocess.CalledProcessError as exc:
        raise SetupError(f"Command failed with exit code {exc.returncode}") from exc


def command_output(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SetupError(f"Could not execute {' '.join(command)}") from exc

    return completed.stdout.strip()


def parse_version(raw_version: str, command_name: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", raw_version)
    if match is None:
        raise SetupError(
            f"Could not identify the {command_name} version from: {raw_version!r}"
        )
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def validate_python() -> str:
    current_version = sys.version_info[:3]
    if current_version < MINIMUM_PYTHON:
        raise SetupError(
            "Python 3.11 or newer is required; "
            f"found {'.'.join(map(str, current_version))}"
        )

    version = ".".join(map(str, current_version))
    print(f"[ok] Python {version}")
    return version


def validate_node() -> str:
    node = shutil.which("node")
    if node is None:
        raise SetupError("Node.js was not found in PATH")

    raw_version = command_output([node, "--version"])
    version = parse_version(raw_version, "Node.js")
    supported = (version[0] == 20 and version >= (20, 19, 0)) or version >= (
        22,
        12,
        0,
    )
    if not supported:
        raise SetupError(
            f"Node.js 20.19+ or 22.12+ is required; found {'.'.join(map(str, version))}"
        )

    formatted_version = ".".join(map(str, version))
    print(f"[ok] Node.js {formatted_version}")
    return formatted_version


def validate_npm() -> tuple[str, str]:
    npm = shutil.which("npm")
    if npm is None:
        raise SetupError("npm was not found in PATH")

    version = command_output([npm, "--version"])
    print(f"[ok] npm {version}")
    return npm, version


def read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        name, separator, value = line.partition("=")
        if separator and name.strip():
            values[name.strip()] = value.strip()

    return values


def provider_base_url() -> str:
    env_values = read_env_file(BACKEND_DIR / ".env")
    return os.getenv(
        "PROVIDER_BASE_URL",
        env_values.get("PROVIDER_BASE_URL", DEFAULT_PROVIDER_BASE_URL),
    ).rstrip("/")


def validate_provider_access() -> None:
    request = Request(
        f"{provider_base_url()}/users/1",
        headers={"User-Agent": "fast-api-users-setup"},
    )

    try:
        with urlopen(request, timeout=5) as response:
            if not 200 <= response.status < 300:
                raise SetupError(
                    f"The provider returned an unexpected HTTP {response.status}"
                )
    except HTTPError as exc:
        raise SetupError(f"The provider returned HTTP {exc.code}") from exc
    except (OSError, URLError, ValueError) as exc:
        raise SetupError("Could not access the configured external provider") from exc

    print("[ok] External provider is accessible")


def copy_environment_example(example: Path, destination: Path) -> None:
    if destination.exists():
        print(f"[keep] Existing {destination.relative_to(PROJECT_ROOT)}")
        return

    shutil.copyfile(example, destination)
    print(f"[created] {destination.relative_to(PROJECT_ROOT)}")


def virtual_environment_python() -> Path:
    virtual_environment = BACKEND_DIR / ".venv"
    python_path = (
        virtual_environment / "Scripts" / "python.exe"
        if os.name == "nt"
        else virtual_environment / "bin" / "python"
    )

    if not virtual_environment.exists():
        run([sys.executable, "-m", "venv", str(virtual_environment)])
    elif not python_path.exists():
        raise SetupError(
            "backend/.venv exists but is not a valid virtual environment; "
            "remove or rename it and run the setup again"
        )
    else:
        print("[keep] Existing backend/.venv")

    return python_path


def install_project(npm: str) -> None:
    copy_environment_example(
        BACKEND_DIR / ".env.example",
        BACKEND_DIR / ".env",
    )
    copy_environment_example(
        FRONTEND_DIR / ".env.example",
        FRONTEND_DIR / ".env.local",
    )

    python_path = virtual_environment_python()
    run([str(python_path), "-m", "pip", "install", "-e", ".[dev]"], cwd=BACKEND_DIR)
    run([npm, "ci"], cwd=FRONTEND_DIR)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate requirements and configure the project locally."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate requirements without creating or installing anything",
    )
    parser.add_argument(
        "--skip-provider-check",
        action="store_true",
        help="skip the external provider connectivity check",
    )
    return parser.parse_args()


def print_summary(
    python_version: str,
    node_version: str,
    npm_version: str,
    provider_status: str,
    *,
    installed: bool,
) -> None:
    print("\nResumo da configuração")
    print(
        f"  Requisitos: Python {python_version} | "
        f"Node.js {node_version} | npm {npm_version}"
    )
    print(f"  Provider: {provider_status}")

    if not installed:
        print("  Arquivos do projeto: nenhuma alteração")
        return

    print("  Backend: .env pronto | ambiente virtual pronto | dependências instaladas")
    print("  Frontend: .env.local pronto | dependências instaladas")
    print("\nPróximo passo (em outro terminal)")
    print("  python scripts/run.py")
    print("  Backend:  http://localhost:8000")
    print("  Frontend: http://localhost:5173")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    arguments = parse_arguments()

    try:
        print("Validating project requirements...")
        python_version = validate_python()
        node_version = validate_node()
        npm, npm_version = validate_npm()

        if arguments.skip_provider_check:
            print("[skip] External provider connectivity check")
            provider_status = "verificação de conectividade ignorada"
        else:
            validate_provider_access()
            provider_status = "acessível"

        if arguments.check_only:
            print_summary(
                python_version,
                node_version,
                npm_version,
                provider_status,
                installed=False,
            )
            return 0

        print("\nConfiguring the project...")
        install_project(npm)
    except SetupError as exc:
        print(f"\nSetup error: {exc}", file=sys.stderr)
        return 1

    print_summary(
        python_version,
        node_version,
        npm_version,
        provider_status,
        installed=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
