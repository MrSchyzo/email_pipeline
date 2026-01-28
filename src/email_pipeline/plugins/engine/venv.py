import shutil
import sys
import time
from pathlib import Path
from typing import Any

from email_pipeline.logger import logger
from email_pipeline.plugins.engine.subprocess_run import subprocess_run
from email_pipeline.plugins.filesystem import compute_file_checksum


def ensure_venv(plugin_dir, is_builtin=False) -> tuple[Any, str] | tuple[Any, Any] | None:
    root = __builtin_venvs_path if is_builtin else __plugin_venvs_path
    venv = (root / plugin_dir.name).resolve()
    python = venv / "bin" / "python"

    requirements_path = plugin_dir / "requirements.txt"
    if not requirements_path.exists():
        return venv, ensure_python(python)

    if not is_requirements_changed(requirements_path) and venv.exists():
        return venv, ensure_python(python)

    logger.info("Plugin is outdated or missing. Recreating virtual environment.",
                extra={"plugin": plugin_dir.name, "venv": venv.resolve()})

    start = time.perf_counter_ns()
    if venv.exists():
        shutil.rmtree(venv)

    subprocess_run([sys.executable, "-m", "venv", venv], expect_success=True)
    subprocess_run([venv / "bin" / "pip", "install", "-r", requirements_path], expect_success=True)
    subprocess_run([venv / "bin" / "pip", "install", "--upgrade", "certifi"], expect_success=True)

    save_current_checksum(requirements_path, compute_file_checksum(requirements_path))

    elapsed = (time.perf_counter_ns() - start) / 1e6
    logger.info("Virtual environment created.",
                extra={"plugin": plugin_dir.name, "venv": venv.resolve(), "elapsed_ms": elapsed})
    return venv, ensure_python(python)


def ensure_python(python):
    if not python.exists():
        python = sys.executable
    return python


def is_requirements_changed(requirements_path: Path) -> bool:
    return get_current_checksum(requirements_path) != compute_file_checksum(requirements_path)


def get_current_checksum(requirements_path: Path) -> str | None:
    checksum_file = requirements_path.parent / __checksum_file
    if not checksum_file.exists():
        return None
    return checksum_file.read_text().strip()


def save_current_checksum(requirements_path: Path, checksum: str):
    checksum_file = requirements_path.parent / __checksum_file
    checksum_file.write_text(checksum)


__checksum_file = ".install_checksum"
__plugin_venvs_path = Path("plugin_envs")
__builtin_venvs_path = Path("builtin_envs")
