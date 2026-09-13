"""File item data model for tracking scanned and organized files."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileItem:
    """Represents a file detected during scanning with its movement status."""
    name: str
    full_path: str
    extension: str
    size_bytes: int
    modified_time: float
    category: str = "Other"
    reason: str = ""
    is_hidden: bool = False
    selected: bool = True
    proposed_destination: str = ""
    final_destination: str = ""
    status: str = "Ready"  # Ready, Moved, Skipped, Error, Excluded
    error_message: str = ""

    @property
    def path(self) -> Path:
        return Path(self.full_path)

    @property
    def proposed_path(self) -> Path:
        return Path(self.proposed_destination) if self.proposed_destination else Path("")
