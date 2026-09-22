from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


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


def main() -> int:
    try:
        python_path, npm = validate_project_setup()
    except CheckError as exc:
        print(
            f"Check error: {exc}. Execute 'python scripts/setup.py' first.",
            file=sys.stderr,
        )
        return 1

    try:
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
