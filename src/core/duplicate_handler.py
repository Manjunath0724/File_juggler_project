"""Duplicate resolution and collision handling logic."""
from pathlib import Path
from src.models.organization_rule import DuplicatePolicy


class DuplicateHandler:
    """Handles existing file collisions according to chosen policies."""

    @staticmethod
    def get_unique_path(target_path: Path) -> Path:
        """
        Generate a unique path by appending a counter in the format 'name (n).ext'
        if target_path already exists.
        """
        if not target_path.exists():
            return target_path

        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent

        counter = 1
        while True:
            candidate = parent / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    @classmethod
    def resolve_collision(
        cls,
        target_path: Path,
        policy: DuplicatePolicy = DuplicatePolicy.RENAME
    ) -> tuple[Path, bool, str]:
        """
        Resolve destination conflict when a file with the same name exists at destination.
        
        Returns:
            tuple of (final_path, should_skip, action_description)
        """
        if not target_path.exists():
            return target_path, False, "New file"

        if policy == DuplicatePolicy.SKIP:
            return target_path, True, "Skipped (file exists)"

        if policy == DuplicatePolicy.REPLACE:
            return target_path, False, "Replace existing"

        # Default: RENAME
        unique_path = cls.get_unique_path(target_path)
        return unique_path, False, f"Renamed to {unique_path.name}"
