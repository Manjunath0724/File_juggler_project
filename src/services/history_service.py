"""History persistence and session disband service for File Juggler."""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.models.operation_result import OperationResult, MoveRecord
from src.services.settings_service import get_config_dir


from src.services.encryption_service import EncryptionService


class HistoryService:
    """Manages persistent history of file juggle sessions with client-side encryption."""

    def __init__(self, filename: str = "history.json", config_dir: Optional[Path] = None):
        base_dir = config_dir or get_config_dir()
        self.history_file = base_dir / filename

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve full history list (decrypting if encrypted), newest entries first."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                data = EncryptionService.decrypt_data(content, default=None)
                if data is None:
                    # Fallback to direct json parse
                    data = json.loads(content)
                if isinstance(data, list):
                    return data
                return []
        except Exception:
            return []

    def _save_history(self, history: List[Dict[str, Any]]) -> bool:
        """Persist history list to disk using client-side encryption."""
        try:
            encrypted_payload = EncryptionService.encrypt_data(history)
            with open(self.history_file, "w", encoding="utf-8") as f:
                f.write(encrypted_payload)
            return True
        except Exception:
            return False

    def record_session(self, result: OperationResult) -> bool:
        """
        Record a completed file organization session into persistent history.
        Only records real operations (skips dry-run simulations and empty moves).
        """
        if result.is_dry_run or not result.moves:
            return False

        history = self.get_history()

        # Check if already recorded to avoid duplicates
        for item in history:
            if item.get("session_id") == result.session_id:
                return False

        session_entry: Dict[str, Any] = {
            "session_id": result.session_id,
            "timestamp": result.timestamp,
            "mode": result.mode,
            "source_folder": result.source_folder,
            "destination_folder": result.destination_folder,
            "total_scanned": result.total_scanned,
            "total_moved": result.total_moved,
            "total_skipped": result.total_skipped,
            "total_failed": result.total_failed,
            "duration_seconds": result.duration_seconds,
            "created_folders": list(result.created_folders),
            "status": "active",  # "active" or "disbanded"
            "disbanded_at": None,
            "moves": [
                {
                    "source": m.source,
                    "destination": m.destination,
                    "timestamp": m.timestamp,
                    "file_size": m.file_size,
                    "category": m.category,
                    "original_name": m.original_name,
                    "final_name": m.final_name,
                    "was_renamed": m.was_renamed,
                }
                for m in result.moves
            ],
        }

        # Keep newest first, limit to 100 operations
        history.insert(0, session_entry)
        if len(history) > 100:
            history = history[:100]

        return self._save_history(history)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Look up a specific session by ID."""
        for item in self.get_history():
            if item.get("session_id") == session_id:
                return item
        return None

    def mark_session_disbanded(self, session_id: str) -> bool:
        """Mark a session as disbanded without re-executing moves (e.g. after UndoManager)."""
        history = self.get_history()
        updated = False
        for item in history:
            if item.get("session_id") == session_id:
                item["status"] = "disbanded"
                item["disbanded_at"] = datetime.now().isoformat()
                updated = True
                break
        if updated:
            return self._save_history(history)
        return False

    def disband_session(
        self,
        session_id: str,
        progress_callback: Optional[callable] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Disband (revert) a specific juggle operation.
        Restores moved files back to their original source locations,
        handles filename collisions safely, prunes created empty folders,
        and marks the session as disbanded.

        Returns:
            (restored_count, error_count, list_of_error_messages)
        """
        history = self.get_history()
        target_session = None
        for item in history:
            if item.get("session_id") == session_id:
                target_session = item
                break

        if not target_session:
            return 0, 1, ["Operation session not found in history."]

        if target_session.get("status") == "disbanded":
            return 0, 1, ["This juggle session has already been disbanded."]

        moves = list(reversed(target_session.get("moves", [])))
        if not moves:
            target_session["status"] = "disbanded"
            target_session["disbanded_at"] = datetime.now().isoformat()
            self._save_history(history)
            return 0, 0, []

        restored = 0
        errors: List[str] = []
        total = len(moves)

        for idx, move in enumerate(moves, start=1):
            curr_path = Path(move["destination"])
            orig_path = Path(move["source"])

            if progress_callback:
                progress_callback(idx, total, orig_path.name)

            if not curr_path.exists():
                errors.append(f"Cannot restore {curr_path.name}: file is missing at destination.")
                continue

            # Ensure original directory exists
            try:
                orig_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Failed to access source directory {orig_path.parent}: {e}")
                continue

            # Check if original path is currently occupied to avoid data loss
            final_restore_path = orig_path
            if final_restore_path.exists():
                stem = orig_path.stem
                suffix = orig_path.suffix
                counter = 1
                while final_restore_path.exists():
                    final_restore_path = orig_path.parent / f"{stem}_restored_{counter}{suffix}"
                    counter += 1

            try:
                shutil.move(str(curr_path), str(final_restore_path))
                restored += 1
            except Exception as e:
                errors.append(f"Error restoring {curr_path.name}: {e}")

        # Clean up empty folders that were created during this session
        created_folders = target_session.get("created_folders", [])
        for folder_str in reversed(created_folders):
            try:
                folder = Path(folder_str)
                if folder.exists() and folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
            except Exception:
                pass

        # Update session status
        target_session["status"] = "disbanded"
        target_session["disbanded_at"] = datetime.now().isoformat()
        target_session["restored_count"] = restored

        self._save_history(history)
        return restored, len(errors), errors

    def delete_session(self, session_id: str) -> bool:
        """Remove a session from history."""
        history = self.get_history()
        filtered = [item for item in history if item.get("session_id") != session_id]
        if len(filtered) != len(history):
            return self._save_history(filtered)
        return False

    def clear_history(self) -> bool:
        """Clear all history entries."""
        return self._save_history([])
