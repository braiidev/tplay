import os
import json

PLAYLIST_FILE = os.path.join(os.path.expanduser("~/.config/player"), "playlist.json")


def load_all() -> tuple[dict, str]:
    try:
        with open(PLAYLIST_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"default": []}, "default"

    pls = data.get("playlists", [])
    active = data.get("active", "default")
    result = {}
    if not pls:
        return {"default": []}, "default"
    for pl in pls:
        name = pl.get("name", "default")
        songs = pl.get("songs", [])
        valid = []
        for s in songs:
            if os.path.exists(s):
                valid.append((os.path.basename(s), s))
        result[name] = valid
    if active not in result:
        active = next(iter(result.keys()), "default")
    return result, active


def save_all(playlist_data: dict, active_name: str) -> None:
    pls = [{"name": name, "songs": [path for _, path in songs]}
           for name, songs in playlist_data.items()]
    data = {"active": active_name, "playlists": pls}
    try:
        with open(PLAYLIST_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
