from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SHUTDOWN_TIMEOUT_SECONDS = 5


class RunError(RuntimeError):
    """Raised when the project is not ready to run."""


def backend_python() -> Path:
    virtual_environment = BACKEND_DIR / ".venv"
    python_path = (
        virtual_environment / "Scripts" / "python.exe"
        if os.name == "nt"
        else virtual_environment / "bin" / "python"
    )

    if not python_path.exists():
        raise RunError("Backend virtual environment not found")
    return python_path


def npm_command() -> str:
    npm = shutil.which("npm")
    if npm is None:
        raise RunError("npm was not found in PATH")
    return npm


def validate_project_setup() -> tuple[Path, str]:
    python_path = backend_python()
    npm = npm_command()

    if not (FRONTEND_DIR / "node_modules").is_dir():
        raise RunError("Frontend dependencies were not installed")
    if not (FRONTEND_DIR / ".env.local").is_file():
        raise RunError("frontend/.env.local was not created")

    return python_path, npm


def start_process(command: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    if os.name == "nt":
        return subprocess.Popen(
            command,
            cwd=cwd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(command, cwd=cwd, start_new_session=True)


def stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=SHUTDOWN_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        process.kill()
        process.wait()


def wait_for_processes(processes: dict[str, subprocess.Popen[bytes]]) -> None:
    while True:
        for name, process in processes.items():
            exit_code = process.poll()
            if exit_code is not None:
                raise RunError(f"{name} stopped with exit code {exit_code}")
        time.sleep(0.25)


def main() -> int:
    try:
        python_path, npm = validate_project_setup()
    except RunError as exc:
        print(
            f"Run error: {exc}. Execute 'python scripts/setup.py' first.",
            file=sys.stderr,
        )
        return 1

    processes: dict[str, subprocess.Popen[bytes]] = {}
    return_code = 0

    try:
        print("Starting backend at http://localhost:8000")
        processes["Backend"] = start_process(
            [
                str(python_path),
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--port",
                "8000",
            ],
            BACKEND_DIR,
        )

        print("Starting frontend at http://localhost:5173")
        processes["Frontend"] = start_process(
            [npm, "run", "dev", "--", "--strictPort"],
            FRONTEND_DIR,
        )

        print("Both applications are running. Press Ctrl+C to stop them.")
        wait_for_processes(processes)
    except KeyboardInterrupt:
        print("\nStopping applications...")
    except (OSError, RunError) as exc:
        print(f"\nRun error: {exc}", file=sys.stderr)
        return_code = 1
    finally:
        for process in processes.values():
            stop_process(process)

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
