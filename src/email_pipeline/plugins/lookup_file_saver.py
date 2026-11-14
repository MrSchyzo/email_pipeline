import copy
import json
from pathlib import Path

from email_pipeline.logger import logger
from email_pipeline.plugins.filesystem import save_bytes


class LookupFileSaver:
    def __init__(self, directory_lookup: dict[str, str]):
        self.lookup = copy.deepcopy(directory_lookup)
        self.logger = logger
        if "otherwise" not in self.lookup:
            self.logger.warning("No 'otherwise' branch specified in lookup, defaulting to '.'")
            self.lookup["otherwise"] = "."

    @classmethod
    def from_json_config(cls, config_file: str | Path, root: str = ".") -> "LookupFileSaver":
        """Relative paths in config are resolved against `root`, which is also the 'otherwise' default."""
        config_path = Path(config_file)
        paths = {}
        if config_path.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            paths = config.get('paths', {})
        else:
            logger.warning("Config file not found, defaulting to empty lookup", extra={"config_file": str(config_path.resolve())})

        paths.setdefault("otherwise", ".")
        # joining onto an absolute path returns it unchanged
        return cls({key: str(Path(root) / path) for key, path in paths.items()})

    def save_file(self, filename: str, content: bytes, key: str | None = None, src: str | Path | None = None):
        """`src` is only logged: pass the source file path when there is one (None for downloaded bytes)."""
        directory = self.lookup["otherwise"]
        if key:
            directory = self.lookup.get(key, directory)
        save_bytes(Path(directory) / filename, content, src)