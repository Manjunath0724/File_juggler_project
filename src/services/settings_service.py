"""Configuration and preferences persistence service."""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any


def get_config_dir() -> Path:
    """Get the persistent app data configuration directory."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        config_path = Path(base) / "FileJuggler"
    else:
        config_path = Path.home() / ".config" / "filejuggler"
    
    try:
        config_path.mkdir(parents=True, exist_ok=True)
    except Exception:
        config_path = Path.cwd() / ".config"
        config_path.mkdir(parents=True, exist_ok=True)

    return config_path


DEFAULT_SETTINGS: Dict[str, Any] = {
    "last_source_folder": "",
    "last_destination_folder": "",
    "organization_mode": "file_type",
    "include_subfolders": False,
    "include_hidden_files": False,
    "duplicate_policy": "rename",
    "theme": "dark",
    "dry_run": False,
    "excluded_extensions": [".tmp", ".part", ".crdownload", ".bak"],
    "excluded_folders": ["node_modules", ".git", "$RECYCLE.BIN", "__pycache__", ".venv"],
    "combined_pattern": "type_then_size",
}


from src.services.encryption_service import EncryptionService


class SettingsService:
    """Handles loading and saving user configuration settings to disk with client-side encryption."""

    def __init__(self, filename: str = "settings.json"):
        self.config_file = get_config_dir() / filename

    def load(self) -> Dict[str, Any]:
        """Load user settings (decrypting if encrypted) or return defaults if not found."""
        if not self.config_file.exists():
            return dict(DEFAULT_SETTINGS)

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                saved = EncryptionService.decrypt_data(content, default=None)
                if saved is None:
                    # Fallback to direct json parse
                    saved = json.loads(content)
                settings = dict(DEFAULT_SETTINGS)
                if isinstance(saved, dict):
                    settings.update(saved)
                return settings
        except Exception:
            return dict(DEFAULT_SETTINGS)

    def save(self, settings: Dict[str, Any]) -> bool:
        """Save settings dictionary to disk using client-side encryption."""
        try:
            encrypted_payload = EncryptionService.encrypt_data(settings)
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(encrypted_payload)
            return True
        except Exception:
            return False
