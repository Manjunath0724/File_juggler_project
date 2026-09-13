"""Undo manager providing full transaction rollback for file movements."""
import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from src.models.operation_result import OperationResult, MoveRecord


class UndoManager:
    """Manages rollback of file operations."""

    def __init__(self):
        self._history: List[OperationResult] = []

    def record_session(self, result: OperationResult) -> None:
        """Store completed operation result in undo history."""
        if result.moves and not result.is_dry_run:
            self._history.append(result)

    def can_undo(self) -> bool:
        """Returns True if there is a session available to undo."""
        return len(self._history) > 0

    def get_last_session(self) -> Optional[OperationResult]:
        """Returns the most recent operation result without removing it."""
        return self._history[-1] if self._history else None

    def undo_last(
        self,
        progress_callback: Optional[callable] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Undo the most recent operation session.
        Returns:
            (restored_count, error_count, list_of_error_messages)
        """
        if not self._history:
            return 0, 0, ["No operations available to undo."]

        last_session = self._history.pop()
        moves = list(reversed(last_session.moves))

        restored = 0
        errors: List[str] = []
        total = len(moves)

        for idx, move in enumerate(moves, start=1):
            curr_path = Path(move.destination)
            orig_path = Path(move.source)

            if progress_callback:
                progress_callback(idx, total, orig_path.name)

            if not curr_path.exists():
                errors.append(f"Cannot restore {curr_path.name}: file was moved or deleted from destination.")
                continue

            # Ensure original directory exists
            try:
                orig_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Failed to create original directory {orig_path.parent}: {e}")
                continue

            # Check if original path is currently occupied
            final_restore_path = orig_path
            if final_restore_path.exists():
                # Destination already occupied at original place, append suffix
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

        # Clean up empty folders that were created during the session
        for folder_str in reversed(last_session.created_folders):
            try:
                folder = Path(folder_str)
                if folder.exists() and folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()
            except Exception:
                pass

        return restored, len(errors), errors

    def clear_history(self) -> None:
        """Clear all undo history."""
        self._history.clear()
