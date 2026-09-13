"""File system utilities, safe path checks, and Windows helpers."""
import os
import stat
import sys
from pathlib import Path
from typing import Optional


def get_default_downloads_folder() -> str:
    """Retrieve the path to the user's Downloads directory across platforms."""
    downloads_path = Path.home() / "Downloads"
    if downloads_path.exists():
        return str(downloads_path.resolve())
    return str(Path.home().resolve())


def is_file_hidden(file_path: Path) -> bool:
    """Check if a file or folder is marked as hidden (supports dot-files and Windows attribute)."""
    try:
        # Check standard unix/dot convention
        if file_path.name.startswith("."):
            return True

        # Check Windows hidden attribute
        if sys.platform == "win32" and file_path.exists():
            attrs = os.stat(str(file_path)).st_file_attributes
            if attrs & stat.FILE_ATTRIBUTE_HIDDEN:
                return True
    except (OSError, AttributeError):
        pass
    return False


def is_safe_to_organize(source_path: str) -> tuple[bool, str]:
    """Validate that the given folder is valid and not a critical system root."""
    try:
        p = Path(source_path).resolve()
        if not p.exists():
            return False, "Selected folder does not exist."
        if not p.is_dir():
            return False, "Selected path is a file, not a directory."

        # Check Windows root and critical system directories
        root_parts = p.parts
        if len(root_parts) <= 1:
            return False, "Cannot organize the drive root directly (e.g. C:\\). Please select a subfolder."

        drive = p.drive.upper()
        lower_path = str(p).lower()

        dangerous = [
            r"c:\windows",
            r"c:\program files",
            r"c:\program files (x86)",
            r"c:\system volume information",
            r"c:\recovery",
            r"c:\users\all users",
            r"c:\users\default",
        ]
        for d in dangerous:
            if lower_path == d or lower_path.startswith(d + "\\"):
                return False, f"Accessing critical system directory '{p}' is restricted for safety."

        return True, ""
    except Exception as e:
        return False, str(e)


def is_subpath(child: Path, parent: Path) -> bool:
    """Check if child is inside parent."""
    try:
        child_res = child.resolve()
        parent_res = parent.resolve()
        return parent_res in child_res.parents or child_res == parent_res
    except Exception:
        return False
