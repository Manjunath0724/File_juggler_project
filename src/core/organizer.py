"""Core organizer module responsible for safe file moves, folder creation, and tracking."""
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import List, Callable, Optional, Set

from src.models.file_item import FileItem
from src.models.operation_result import OperationResult, MoveRecord
from src.models.organization_rule import OrganizationConfig, DuplicatePolicy
from src.core.duplicate_handler import DuplicateHandler


class FileOrganizer:
    """Executes file movements safely, maintaining an undoable transaction record."""

    def __init__(self, config: Optional[OrganizationConfig] = None):
        self.config = config or OrganizationConfig()

    def organize(
        self,
        items: List[FileItem],
        source_folder: str,
        destination_folder: str,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> OperationResult:
        """
        Execute file movement for all selected items.
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())[:8]

        result = OperationResult(
            session_id=session_id,
            mode=self.config.mode.value,
            source_folder=source_folder,
            destination_folder=destination_folder,
            is_dry_run=self.config.dry_run,
        )

        selected_items = [item for item in items if item.selected]
        result.total_scanned = len(items)
        total_to_move = len(selected_items)

        created_dirs: Set[str] = set()

        for idx, item in enumerate(selected_items, start=1):
            if should_cancel and should_cancel():
                break

            source_path = Path(item.full_path)
            target_path = Path(item.proposed_destination)

            if progress_callback:
                progress_callback(idx, total_to_move, item.name, f"Processing {item.name}")

            # Verify source still exists
            if not source_path.exists():
                item.status = "Error"
                item.error_message = "Source file no longer exists"
                result.total_failed += 1
                result.errors.append({"file": item.name, "error": item.error_message})
                continue

            # Check if source is identical to destination
            try:
                if source_path.resolve() == target_path.resolve():
                    item.status = "Skipped"
                    item.error_message = "File is already at destination"
                    result.total_skipped += 1
                    continue
            except Exception:
                pass

            # Resolve collisions
            final_target, should_skip, action_msg = DuplicateHandler.resolve_collision(
                target_path,
                self.config.duplicate_policy
            )

            if should_skip:
                item.status = "Skipped"
                item.error_message = action_msg
                result.total_skipped += 1
                continue

            # Ensure target parent directory exists
            target_parent = final_target.parent
            if not target_parent.exists():
                if not self.config.dry_run:
                    try:
                        target_parent.mkdir(parents=True, exist_ok=True)
                        created_dirs.add(str(target_parent))
                    except (OSError, PermissionError) as e:
                        item.status = "Error"
                        item.error_message = f"Failed to create directory {target_parent.name}: {e}"
                        result.total_failed += 1
                        result.errors.append({"file": item.name, "error": item.error_message})
                        continue
                else:
                    created_dirs.add(str(target_parent))

            # Perform the move or simulate dry-run
            was_renamed = (final_target.name != source_path.name)
            if self.config.dry_run:
                item.status = "Dry Run"
                item.final_destination = str(final_target)
                result.total_moved += 1
                result.moves.append(
                    MoveRecord(
                        source=str(source_path),
                        destination=str(final_target),
                        timestamp=time.time(),
                        file_size=item.size_bytes,
                        category=item.category,
                        original_name=item.name,
                        final_name=final_target.name,
                        was_renamed=was_renamed,
                    )
                )
            else:
                try:
                    # Safe move
                    shutil.move(str(source_path), str(final_target))
                    item.status = "Moved"
                    item.final_destination = str(final_target)
                    result.total_moved += 1

                    result.moves.append(
                        MoveRecord(
                            source=str(source_path),
                            destination=str(final_target),
                            timestamp=time.time(),
                            file_size=item.size_bytes,
                            category=item.category,
                            original_name=item.name,
                            final_name=final_target.name,
                            was_renamed=was_renamed,
                        )
                    )
                except (PermissionError, OSError) as e:
                    item.status = "Error"
                    item.error_message = f"Permission or OS error: {e}"
                    result.total_failed += 1
                    result.errors.append({"file": item.name, "error": str(e)})

        result.created_folders = sorted(list(created_dirs))
        result.duration_seconds = round(time.time() - start_time, 2)
        return result
