"""Classification engine that determines target subfolders for files."""
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from src.models.file_item import FileItem
from src.models.organization_rule import OrganizationConfig, OrganizationMode
from src.utils.size_utils import classify_size


# Granular document, image, and media extension maps
EXTENSIONS_MAP: Dict[str, List[str]] = {
    # Document subcategories
    "PDF Documents": [".pdf"],
    "Excel & Spreadsheets": [".xlsx", ".xls", ".csv", ".ods", ".tsv", ".xlsm", ".xlsb", ".numbers"],
    "Word Documents": [".docx", ".doc", ".rtf", ".odt", ".pages", ".dotx"],
    "PowerPoint Presentations": [".pptx", ".ppt", ".odp", ".key", ".pps", ".ppsx"],
    "Text & Notes": [".txt", ".md", ".log", ".tex", ".markdown"],

    # Image subcategories
    "Photos & Images": [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".jfif", ".avif"],
    "Vector Graphics": [".svg", ".ai", ".eps", ".cdr"],
    "GIFs & Animations": [".gif", ".apng"],
    "RAW Camera Files": [".raw", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2", ".pef", ".raf"],
    "Design & Project Files": [".psd", ".psb", ".sketch", ".fig", ".xd", ".blend"],
    "Icons": [".ico", ".icns"],

    # Media, System, and Code
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp", ".ts"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus", ".alac", ".aiff"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".tgz", ".dmg"],
    "Applications": [".exe", ".msi", ".bat", ".cmd", ".com", ".appinstaller"],
    "Code": [".py", ".java", ".cpp", ".c", ".h", ".cs", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json", ".xml", ".sql", ".sh", ".php", ".rs", ".go", ".rb", ".yaml", ".yml", ".dart", ".kt"],
}

# Optional parent mapping for nested grouping (e.g. Documents/PDF, Images/Photos)
PARENT_GROUP_MAP: Dict[str, str] = {
    "PDF Documents": "Documents/PDF",
    "Excel & Spreadsheets": "Documents/Excel",
    "Word Documents": "Documents/Word",
    "PowerPoint Presentations": "Documents/Presentations",
    "Text & Notes": "Documents/Text",
    "Photos & Images": "Images/Photos",
    "Vector Graphics": "Images/Vector",
    "GIFs & Animations": "Images/GIFs",
    "RAW Camera Files": "Images/RAW",
    "Design & Project Files": "Images/Design",
    "Icons": "Images/Icons",
}


class FileClassifier:
    """Classifies files into appropriate subfolders based on rules."""

    def __init__(self, config: Optional[OrganizationConfig] = None):
        self.config = config or OrganizationConfig()
        # Build inverted extension index for O(1) lookup
        self._ext_to_category: Dict[str, str] = {}
        for category, exts in EXTENSIONS_MAP.items():
            for ext in exts:
                self._ext_to_category[ext.lower()] = category

    def classify_by_type(self, item: FileItem) -> tuple[str, str]:
        """Classify item by extension into specific granular categories."""
        ext = item.extension.lower()
        if not ext:
            return "Other", "No file extension"
        category = self._ext_to_category.get(ext, "Other")
        if getattr(self.config, "nested_subcategories", False):
            category = PARENT_GROUP_MAP.get(category, category)
        return category, f"Extension {ext.upper()}"

    def classify_by_size(self, item: FileItem) -> tuple[str, str]:
        """Classify item by size bracket."""
        category = classify_size(item.size_bytes, self.config.size_thresholds)
        return category, f"Size bracket ({category})"

    def classify_by_date(self, item: FileItem) -> tuple[str, str]:
        """Classify item by modification timestamp."""
        file_date = date.fromtimestamp(item.modified_time)
        today = date.today()
        diff = (today - file_date).days

        if diff == 0:
            category = "Today"
        elif diff == 1:
            category = "Yesterday"
        elif diff <= 7:
            category = "This Week"
        elif diff <= 30:
            category = "This Month"
        elif file_date.year == today.year:
            category = f"{file_date.strftime('%B %Y')}"
        else:
            category = f"{file_date.year}"

        return category, f"Modified on {file_date.isoformat()}"

    def classify_combined(self, item: FileItem) -> tuple[str, str]:
        """Classify item using combined hierarchical rules (e.g. Type/Size or Date/Type)."""
        pattern = self.config.combined_pattern

        if pattern == "date_then_type":
            date_cat, _ = self.classify_by_date(item)
            type_cat, _ = self.classify_by_type(item)
            category = f"{date_cat}/{type_cat}"
            reason = f"Date ({date_cat}) and Type ({type_cat})"
        elif pattern == "size_then_type":
            size_cat, _ = self.classify_by_size(item)
            type_cat, _ = self.classify_by_type(item)
            category = f"{size_cat}/{type_cat}"
            reason = f"Size ({size_cat}) and Type ({type_cat})"
        else:  # default: type_then_size
            type_cat, _ = self.classify_by_type(item)
            size_cat, _ = self.classify_by_size(item)
            category = f"{type_cat}/{size_cat}"
            reason = f"Type ({type_cat}) and Size ({size_cat})"

        return category, reason

    def assign_destination(self, item: FileItem, destination_base: str) -> None:
        """
        Determine category, reason, and proposed destination path for the item.
        """
        mode = self.config.mode

        if mode == OrganizationMode.BY_SIZE:
            category, reason = self.classify_by_size(item)
        elif mode == OrganizationMode.BY_DATE:
            category, reason = self.classify_by_date(item)
        elif mode == OrganizationMode.COMBINED:
            category, reason = self.classify_combined(item)
        else:  # default: BY_TYPE
            category, reason = self.classify_by_type(item)

        item.category = category
        item.status = "Ready"

        dest_dir = Path(destination_base) / category
        item.proposed_destination = str(dest_dir / item.name)

    def classify_all(self, items: List[FileItem], destination_base: str) -> List[FileItem]:
        """Classify all items and populate their destination paths."""
        for item in items:
            self.assign_destination(item, destination_base)
        return items
