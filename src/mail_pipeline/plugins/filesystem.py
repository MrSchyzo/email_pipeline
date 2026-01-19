import hashlib
import os
import time
from pathlib import Path

def ensure_directory(path: str | Path) -> str | Path:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

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