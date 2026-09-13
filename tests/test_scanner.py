"""Tests for the FileScanner module."""
import tempfile
import unittest
from pathlib import Path

from src.models.organization_rule import OrganizationConfig
from src.core.scanner import FileScanner


class TestFileScanner(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

        # Create dummy directory structure
        (self.base_path / "img1.png").write_text("image")
        (self.base_path / "notes.txt").write_text("text")
        (self.base_path / "temp.tmp").write_text("temp")
        (self.base_path / ".hidden_file.txt").write_text("hidden")

        sub = self.base_path / "subfolder"
        sub.mkdir()
        (sub / "sub_doc.pdf").write_text("pdf")

        excluded_sub = self.base_path / "node_modules"
        excluded_sub.mkdir()
        (excluded_sub / "package.json").write_text("{}")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_folder_scan(self):
        config = OrganizationConfig(include_subfolders=False, include_hidden_files=False)
        scanner = FileScanner(config)
        items = scanner.scan(str(self.base_path))

        names = {item.name for item in items}
        self.assertIn("img1.png", names)
        self.assertIn("notes.txt", names)
        self.assertNotIn("temp.tmp", names)  # .tmp is excluded by default
        self.assertNotIn(".hidden_file.txt", names)  # hidden
        self.assertNotIn("sub_doc.pdf", names)  # in subfolder

    def test_recursive_scan_with_exclusions(self):
        config = OrganizationConfig(include_subfolders=True, include_hidden_files=False)
        scanner = FileScanner(config)
        items = scanner.scan(str(self.base_path))

        names = {item.name for item in items}
        self.assertIn("img1.png", names)
        self.assertIn("notes.txt", names)
        self.assertIn("sub_doc.pdf", names)
        self.assertNotIn("package.json", names)  # inside node_modules (excluded folder)

    def test_hidden_file_inclusion(self):
        config = OrganizationConfig(include_subfolders=False, include_hidden_files=True)
        scanner = FileScanner(config)
        items = scanner.scan(str(self.base_path))

        names = {item.name for item in items}
        self.assertIn(".hidden_file.txt", names)


if __name__ == "__main__":
    unittest.main()
