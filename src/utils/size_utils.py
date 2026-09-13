"""Utilities for formatting and categorizing file sizes."""
from typing import Dict, Optional


def format_size(size_bytes: int) -> str:
    """Format size in bytes to a human-readable string (e.g. 4.2 MB)."""
    if size_bytes < 0:
        return "0 B"
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size_bytes)
    unit_index = 0

    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} B"
    elif value >= 100:
        return f"{value:.0f} {units[unit_index]}"
    else:
        return f"{value:.1f} {units[unit_index]}"


DEFAULT_SIZE_THRESHOLDS = {
    "Tiny (<1 MB)": 1 * 1024 * 1024,
    "Small (1-10 MB)": 10 * 1024 * 1024,
    "Medium (10-100 MB)": 100 * 1024 * 1024,
    "Large (100 MB - 1 GB)": 1024 * 1024 * 1024,
}


def classify_size(size_bytes: int, thresholds: Optional[Dict[str, int]] = None) -> str:
    """Categorize a file size based on configured thresholds."""
    if thresholds is None:
        thresholds = DEFAULT_SIZE_THRESHOLDS

    # Expect thresholds to be sorted or we sort by value
    sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1])
    for label, limit in sorted_thresholds:
        if size_bytes < limit:
            return label
    return "Huge (>1 GB)"
