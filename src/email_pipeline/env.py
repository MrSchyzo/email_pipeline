from pathlib import Path

def load_env(env_path: Path) -> dict[str, str]:
    env = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env[key] = value
    return env