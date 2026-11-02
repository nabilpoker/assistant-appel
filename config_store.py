"""Stockage local de la clé API dans le profil Windows de l'utilisateur (pas dans le navigateur)."""
import json
import os
from pathlib import Path


def config_path() -> Path:
    base = os.getenv("APPDATA") or str(Path.home())
    folder = Path(base) / "Damia"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "config.json"


def load_config() -> dict:
    p = config_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(data: dict) -> None:
    config_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
