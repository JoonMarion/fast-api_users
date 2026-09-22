from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DEPENDENCY_MARKER = BACKEND_DIR / ".venv" / ".dependency-fingerprint"
DEPENDENCY_FILES = (BACKEND_DIR / "pyproject.toml", FRONTEND_DIR / "package-lock.json")
MINIMUM_PYTHON = (3, 11)


class CheckError(RuntimeError):
    """Raised when the project is not ready to run the checks."""


def backend_python() -> Path:
    virtual_environment = BACKEND_DIR / ".venv"
    python_path = (
        virtual_environment / "Scripts" / "python.exe"
        if os.name == "nt"
        else virtual_environment / "bin" / "python"
    )

    if not python_path.exists():
        raise CheckError("Backend virtual environment not found")
    return python_path


def ensure_backend_python() -> Path:
    virtual_environment = BACKEND_DIR / ".venv"
    if not virtual_environment.exists():
        run_check(
            "Backend virtual environment",
            [sys.executable, "-m", "venv", str(virtual_environment)],
            cwd=PROJECT_ROOT,
        )

    return backend_python()


def npm_command() -> str:
    npm = shutil.which("npm")
    if npm is None:
        raise CheckError("npm was not found in PATH")
    return npm


def validate_project_setup() -> tuple[Path, str]:
    python_path = backend_python()
    npm = npm_command()

    if not (FRONTEND_DIR / "node_modules").is_dir():
        raise CheckError("Frontend dependencies were not installed")

    return python_path, npm


def run_check(name: str, command: list[str], *, cwd: Path) -> None:
    print(f"\n[{name}]", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def run_backend_tests(python_path: Path) -> None:
    with tempfile.TemporaryDirectory(
        prefix="fast-api-users-check-",
        ignore_cleanup_errors=True,
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        run_check(
            "Backend tests",
            [
                str(python_path),
                "-m",
                "pytest",
                "--basetemp",
                str(temporary_root / "pytest"),
                "-o",
                f"cache_dir={temporary_root / 'cache'}",
            ],
            cwd=BACKEND_DIR,
        )


def dependency_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in DEPENDENCY_FILES:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def setup_is_current() -> bool:
    if not (FRONTEND_DIR / "node_modules").is_dir():
        return False

    try:
        backend_python()
        return DEPENDENCY_MARKER.read_text(encoding="utf-8") == dependency_fingerprint()
    except (CheckError, OSError):
        return False


def prepare_project() -> None:
    if setup_is_current():
        print("\n[Project setup]\nDependencies are already synchronized.", flush=True)
        return

    if sys.version_info[:2] < MINIMUM_PYTHON:
        required = ".".join(map(str, MINIMUM_PYTHON))
        current = ".".join(map(str, sys.version_info[:3]))
        raise CheckError(f"Python {required}+ is required; found {current}")

    python_path = ensure_backend_python()
    npm = npm_command()
    run_check(
        "Backend dependencies",
        [str(python_path), "-m", "pip", "install", "-e", ".[dev]"],
        cwd=BACKEND_DIR,
    )
    run_check("Frontend dependencies", [npm, "ci"], cwd=FRONTEND_DIR)
    DEPENDENCY_MARKER.write_text(dependency_fingerprint(), encoding="utf-8")


def main() -> int:
    try:
        prepare_project()
        python_path, npm = validate_project_setup()
        run_check(
            "Ruff lint",
            [
                str(python_path),
                "-m",
                "ruff",
                "check",
                "--config",
                "backend/pyproject.toml",
                "backend",
                "scripts",
            ],
            cwd=PROJECT_ROOT,
        )
        run_check(
            "Ruff format",
            [
                str(python_path),
                "-m",
                "ruff",
                "format",
                "--check",
                "--config",
                "backend/pyproject.toml",
                "backend",
                "scripts",
            ],
            cwd=PROJECT_ROOT,
        )
        run_backend_tests(python_path)
        run_check(
            "Frontend build",
            [npm, "run", "build"],
            cwd=FRONTEND_DIR,
        )
    except CheckError as exc:
        print(f"\nCheck error: {exc}.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"\nCheck failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode
    except OSError as exc:
        print(f"\nCould not execute check: {exc}.", file=sys.stderr)
        return 1

    print("\nAll checks passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
