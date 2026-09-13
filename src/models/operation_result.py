"""Data models for operation results, undo history, and execution summaries."""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class MoveRecord:
    """Represents an individual file move operation for logging and undo."""
    source: str
    destination: str
    timestamp: float
    file_size: int
    category: str
    original_name: str
    final_name: str
    was_renamed: bool = False


@dataclass
class OperationResult:
    """Summary metrics of an organization execution."""
    session_id: str
    mode: str
    source_folder: str
    destination_folder: str
    total_scanned: int = 0
    total_moved: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    duration_seconds: float = 0.0
    created_folders: List[str] = field(default_factory=list)
    moves: List[MoveRecord] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    is_dry_run: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
