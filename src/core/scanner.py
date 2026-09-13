"""Filesystem scanner for detecting files and extracting metadata safely."""
import os
from pathlib import Path
from typing import List, Callable, Optional, Generator

from src.models.file_item import FileItem
from src.models.organization_rule import OrganizationConfig
from src.utils.file_utils import is_file_hidden


class FileScanner:
    """Scans directories and generates FileItem objects according to configuration rules."""

    def __init__(self, config: Optional[OrganizationConfig] = None):
        self.config = config or OrganizationConfig()

    def scan(
        self,
        folder_path: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> List[FileItem]:
        """
        Scan the target folder and return a list of FileItem objects.
        
        Args:
            folder_path: Path to scan.
            progress_callback: Optional callback(scanned_count, current_filename).
            should_cancel: Optional callable that returns True if scan should abort.
        """
        items: List[FileItem] = []
        root = Path(folder_path).resolve()

        if not root.exists() or not root.is_dir():
            return items

        scanned_count = 0
        excluded_exts = {ext.lower().strip() for ext in self.config.excluded_extensions}
        excluded_dirs = {d.lower().strip() for d in self.config.excluded_folders}

        if self.config.include_subfolders:
            walker = os.walk(root)
        else:
            # Single level scan
            try:
                entries = [entry for entry in root.iterdir()]
            except PermissionError:
                return items
            walker = [(str(root), [], [e.name for e in entries if e.is_file()])]

        for current_root_str, subdirs, files in walker:
            if should_cancel and should_cancel():
                break

            current_dir = Path(current_root_str)

            # Filter subdirectories in-place if walking recursively
            if self.config.include_subfolders:
                # Exclude hidden directories if config disallows
                subdirs[:] = [
                    d for d in subdirs
                    if d.lower() not in excluded_dirs
                    and (self.config.include_hidden_files or not is_file_hidden(current_dir / d))
                ]

            for fname in files:
                if should_cancel and should_cancel():
                    break

                file_path = current_dir / fname
                ext = file_path.suffix.lower()

                # Check exclusion by extension
                if ext in excluded_exts:
                    continue

                # Check hidden status
                hidden = is_file_hidden(file_path)
                if hidden and not self.config.include_hidden_files:
                    continue

                try:
                    stats = file_path.stat()
                    size = stats.st_size
                    mtime = stats.st_mtime
                except (OSError, PermissionError) as e:
                    # Skip files that cannot be read
                    continue

                item = FileItem(
                    name=fname,
                    full_path=str(file_path),
                    extension=ext,
                    size_bytes=size,
                    modified_time=mtime,
                    is_hidden=hidden,
                    selected=True,
                )
                items.append(item)
                scanned_count += 1

                if progress_callback:
                    progress_callback(scanned_count, fname)

        return items
