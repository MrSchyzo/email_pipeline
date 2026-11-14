import hashlib
import os
import shutil
import time
from pathlib import Path

from email_pipeline.logger import logger

def ensure_directory(path: str | Path) -> Path:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return Path(path)

def compute_file_checksum(file_path) -> str:
    with open(file_path, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.hexdigest()

def get_latest_file(directory: str | Path, pattern: str | None = None) -> str | None:
    files = find_paths_by_glob(directory, pattern) if pattern else os.listdir(directory)
    return max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f))) if files else None

def find_paths_by_glob(directory: str | Path, pattern: str) -> list[Path]:
    return list(Path(directory).glob(pattern))

def wait_for_new_file(download_dir: str, existing_files: set[str] = [], timeout: float = 15) -> str:
    start_time = time.time()
    wait_delay = 0.1
    while time.time() < start_time + timeout:
        time.sleep(wait_delay)
        current_files = set(os.listdir(download_dir))
        files = current_files - existing_files

        finished_new_files = [f for f in files if not f.endswith(".crdownload")]
        if finished_new_files:
            return os.path.join(download_dir, finished_new_files[0])

    raise TimeoutError(f"Download did not complete within {timeout} seconds in {download_dir}")


# Every plugin output goes through these three functions; control logging in _log_saved.
def save_bytes(dst: str | Path, content: bytes, src: str | Path | None = None) -> Path:
    dst = Path(dst)
    ensure_directory(dst.parent)
    dst.write_bytes(content)
    _log_saved(src, dst)
    return dst


def copy_file(src: str | Path, dst: str | Path) -> Path:
    dst = Path(dst)
    ensure_directory(dst.parent)
    shutil.copy2(src, dst)
    _log_saved(src, dst)
    return dst


def move_file(src: str | Path, dst: str | Path) -> Path:
    dst = Path(dst)
    ensure_directory(dst.parent)
    os.rename(src, dst)
    _log_saved(src, dst)
    return dst


def _log_saved(src: str | Path | None, dst: Path):
    logger.info("Saved file", extra={"src": str(src) if src else None, "dst": str(dst.resolve())},
                stacklevel=3)  # report the plugin line that called save/copy/move
