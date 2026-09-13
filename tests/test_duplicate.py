"""Tests for the DuplicateHandler module."""
import tempfile
import unittest
from pathlib import Path

from src.models.organization_rule import DuplicatePolicy
from src.core.duplicate_handler import DuplicateHandler


class TestDuplicateHandler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_no_collision(self):
        target = self.base_path / "new_file.txt"
        resolved, should_skip, action = DuplicateHandler.resolve_collision(target, DuplicatePolicy.RENAME)
        self.assertEqual(resolved, target)
        self.assertFalse(should_skip)

    def test_rename_policy(self):
        # Create existing file
        existing = self.base_path / "photo.jpg"
        existing.write_text("dummy")

        # Resolve collision
        resolved, should_skip, action = DuplicateHandler.resolve_collision(existing, DuplicatePolicy.RENAME)
        expected = self.base_path / "photo (1).jpg"
        self.assertEqual(resolved, expected)
        self.assertFalse(should_skip)

        # Create photo (1).jpg and test that it generates photo (2).jpg
        expected.write_text("dummy 2")
        resolved2, should_skip2, action2 = DuplicateHandler.resolve_collision(existing, DuplicatePolicy.RENAME)
        self.assertEqual(resolved2, self.base_path / "photo (2).jpg")
        self.assertFalse(should_skip2)

    def test_skip_policy(self):
        existing = self.base_path / "document.pdf"
        existing.write_text("dummy")

        resolved, should_skip, action = DuplicateHandler.resolve_collision(existing, DuplicatePolicy.SKIP)
        self.assertEqual(resolved, existing)
        self.assertTrue(should_skip)

    def test_replace_policy(self):
        existing = self.base_path / "data.csv"
        existing.write_text("dummy")

        resolved, should_skip, action = DuplicateHandler.resolve_collision(existing, DuplicatePolicy.REPLACE)
        self.assertEqual(resolved, existing)
        self.assertFalse(should_skip)


if __name__ == "__main__":
    unittest.main()
