"""Organization rules and mode definitions for File Juggler."""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class OrganizationMode(str, Enum):
    BY_TYPE = "file_type"
    BY_SIZE = "file_size"
    BY_DATE = "date"
    COMBINED = "combined"


class DuplicatePolicy(str, Enum):
    RENAME = "rename"
    SKIP = "skip"
    REPLACE = "replace"


@dataclass
class OrganizationConfig:
    """Configuration options governing how files are scanned and classified."""
    mode: OrganizationMode = OrganizationMode.BY_TYPE
    include_subfolders: bool = False
    include_hidden_files: bool = False
    excluded_extensions: List[str] = field(default_factory=lambda: [".tmp", ".part", ".crdownload", ".bak"])
    excluded_folders: List[str] = field(default_factory=lambda: ["node_modules", ".git", "$RECYCLE.BIN"])
    duplicate_policy: DuplicatePolicy = DuplicatePolicy.RENAME
    dry_run: bool = False
    destination_folder: Optional[str] = None
    
    # Custom thresholds for size mode (in bytes)
    size_thresholds: Dict[str, int] = field(default_factory=lambda: {
        "Tiny": 1 * 1024 * 1024,          # < 1 MB
        "Small": 10 * 1024 * 1024,        # 1 MB - 10 MB
        "Medium": 100 * 1024 * 1024,      # 10 MB - 100 MB
        "Large": 1024 * 1024 * 1024,      # 100 MB - 1 GB
        # > 1 GB is Huge
    })
    
    # Combined mode order: "type_then_size", "size_then_type", "date_then_type"
    combined_pattern: str = "type_then_size"
    nested_subcategories: bool = False
