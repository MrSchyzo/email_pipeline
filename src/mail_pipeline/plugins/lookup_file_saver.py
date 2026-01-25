import copy
import json
from pathlib import Path

from mail_pipeline.logger import logger
from mail_pipeline.plugins.filesystem import ensure_directory


class LookupFileSaver:
    def __init__(self, directory_lookup: dict[str, str]):
        self.lookup = copy.deepcopy(directory_lookup)
        self.logger = logger
        if "otherwise" not in self.lookup:
            self.logger.warning("No 'otherwise' branch specified in lookup, defaulting to '.'")
            self.lookup["otherwise"] = "."

    @classmethod
    def from_json_config(cls, config_file: str | Path, default_directory: str = ".") -> "LookupFileSaver":
        config_path = Path(config_file)
        paths = {}
        if config_path.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            paths = config.get('paths', {})
        else:
            logger.warning("Config file not found, defaulting to empty lookup", extra={"config_file": str(config_path.resolve())})

        if "otherwise" not in paths:
            paths["otherwise"] = default_directory
        return cls(paths)

    def save_file(self, filename: str, content: bytes, key: str | None = None):
        directory = self.lookup["otherwise"]
        if key:
            directory = self.lookup.get(key, directory)
        directory = ensure_directory(directory)
        file_path = directory / filename
        file_path.write_bytes(content)