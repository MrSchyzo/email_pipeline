from pathlib import Path

def load_last_uid(path):
    path = Path(path)
    if not path.exists():
        return 0
    state = path.read_text().strip()
    if not state.isnumeric():
        return 0
    return int(state)

def save_last_uid(path, uid):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(uid))