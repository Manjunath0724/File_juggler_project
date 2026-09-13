"""Tests for FileOrganizer and UndoManager integration."""
import tempfile
import unittest
from pathlib import Path

from src.models.file_item import FileItem
from src.models.organization_rule import OrganizationConfig, OrganizationMode, DuplicatePolicy
from src.core.classifier import FileClassifier
from src.core.organizer import FileOrganizer
from src.core.undo_manager import UndoManager


class TestOrganizerAndUndo(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name) / "source"
        self.source_dir.mkdir()
        self.dest_dir = Path(self.temp_dir.name) / "dest"
        self.dest_dir.mkdir()

        # Create source files
        (self.source_dir / "sample.jpg").write_text("image content")
        (self.source_dir / "manual.pdf").write_text("doc content")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_organize_and_undo(self):
        config = OrganizationConfig(mode=OrganizationMode.BY_TYPE, duplicate_policy=DuplicatePolicy.RENAME)
        classifier = FileClassifier(config)
        organizer = FileOrganizer(config)
        undo_manager = UndoManager()

        # Prepare items
        items = [
            FileItem("sample.jpg", str(self.source_dir / "sample.jpg"), ".jpg", 100, 0.0),
            FileItem("manual.pdf", str(self.source_dir / "manual.pdf"), ".pdf", 200, 0.0),
        ]
        classifier.classify_all(items, str(self.dest_dir))

        # Perform organize
        result = organizer.organize(items, str(self.source_dir), str(self.dest_dir))
        self.assertEqual(result.total_moved, 2)
        self.assertEqual(result.total_failed, 0)

        # Verify files reached destinations
        img_dest = self.dest_dir / "Photos & Images" / "sample.jpg"
        doc_dest = self.dest_dir / "PDF Documents" / "manual.pdf"
        self.assertTrue(img_dest.exists())
        self.assertTrue(doc_dest.exists())
        self.assertFalse((self.source_dir / "sample.jpg").exists())

        # Test Undo
        undo_manager.record_session(result)
        self.assertTrue(undo_manager.can_undo())

        restored, errors, msgs = undo_manager.undo_last()
        self.assertEqual(restored, 2)
        self.assertEqual(errors, 0)

        # Verify files restored back to original source folder
        self.assertTrue((self.source_dir / "sample.jpg").exists())
        self.assertTrue((self.source_dir / "manual.pdf").exists())
        self.assertFalse(img_dest.exists())
        self.assertFalse(doc_dest.exists())

        # Verify empty created folders were cleaned up
        self.assertFalse((self.dest_dir / "Photos & Images").exists())
        self.assertFalse((self.dest_dir / "PDF Documents").exists())


if __name__ == "__main__":
    unittest.main()
