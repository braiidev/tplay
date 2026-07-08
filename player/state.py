import json
import os

from .config import CONFIG_DIR

STATE_FILE = os.path.join(CONFIG_DIR, "state.json")


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return {"playing": False, "file": "", "position": 0}


def save_state(playing: bool, file: str = "", position: int = 0) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({"playing": playing, "file": file, "position": position}, f)
    except (OSError, PermissionError):
        pass
