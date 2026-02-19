from __future__ import annotations

import os
import pathlib

import subprocess


def main() -> None:
    # run the uvicorn CLI with --app-dir so the reloader child process can import `api`
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    app_dir = repo_root / "apps" / "ml-training"
    subprocess.run(
        [
            "uvicorn",
            "api:app",
            "--app-dir",
            str(app_dir),
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
            "--reload",
        ],
        check=True,
    )


# additional entrypoint used by `pyproject.toml` as `start-ml-api`
def start_ml_api() -> None:
    """Start the ml-training API (alias for `main`)."""
    main()
