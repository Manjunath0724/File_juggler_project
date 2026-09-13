"""Tests for HistoryService persistence and disband functionality."""
import tempfile
import unittest
from pathlib import Path

from src.models.operation_result import OperationResult, MoveRecord
from src.services.history_service import HistoryService


class TestHistoryService(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name) / "config"
        self.config_dir.mkdir()

        self.source_dir = Path(self.temp_dir.name) / "source"
        self.source_dir.mkdir()

        self.dest_dir = Path(self.temp_dir.name) / "dest"
        self.dest_dir.mkdir()

        self.history_service = HistoryService(config_dir=self.config_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_and_get_history(self):
        result = OperationResult(
            session_id="test-session-1",
            mode="By File Type & Format",
            source_folder=str(self.source_dir),
            destination_folder=str(self.dest_dir),
            total_scanned=2,
            total_moved=2,
            total_skipped=0,
            total_failed=0,
            duration_seconds=0.15,
            created_folders=[str(self.dest_dir / "PDF Documents")],
            moves=[
                MoveRecord(
                    source=str(self.source_dir / "doc.pdf"),
                    destination=str(self.dest_dir / "PDF Documents" / "doc.pdf"),
                    timestamp=1000.0,
                    file_size=1024,
                    category="PDF Documents",
                    original_name="doc.pdf",
                    final_name="doc.pdf"
                )
            ]
        )

        # Record
        recorded = self.history_service.record_session(result)
        self.assertTrue(recorded)

        # Retrieve
        history = self.history_service.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["session_id"], "test-session-1")
        self.assertEqual(history[0]["status"], "active")
        self.assertEqual(history[0]["total_moved"], 2)

    def test_disband_session_restores_files_and_cleans_folders(self):
        # Prepare actual file in destination
        cat_folder = self.dest_dir / "PDF Documents"
        cat_folder.mkdir()
        dest_file = cat_folder / "report.pdf"
        dest_file.write_text("sample pdf content")

        orig_file_path = self.source_dir / "report.pdf"
        self.assertFalse(orig_file_path.exists())

        result = OperationResult(
            session_id="session-to-disband",
            mode="By File Type & Format",
            source_folder=str(self.source_dir),
            destination_folder=str(self.dest_dir),
            total_scanned=1,
            total_moved=1,
            created_folders=[str(cat_folder)],
            moves=[
                MoveRecord(
                    source=str(orig_file_path),
                    destination=str(dest_file),
                    timestamp=1000.0,
                    file_size=18,
                    category="PDF Documents",
                    original_name="report.pdf",
                    final_name="report.pdf"
                )
            ]
        )

        self.history_service.record_session(result)

        # Disband
        restored, errors, msgs = self.history_service.disband_session("session-to-disband")
        self.assertEqual(restored, 1)
        self.assertEqual(errors, 0)

        # Verify restored file
        self.assertTrue(orig_file_path.exists())
        self.assertEqual(orig_file_path.read_text(), "sample pdf content")
        self.assertFalse(dest_file.exists())

        # Verify empty folder pruned
        self.assertFalse(cat_folder.exists())

        # Verify session status is updated to disbanded
        session = self.history_service.get_session("session-to-disband")
        self.assertIsNotNone(session)
        self.assertEqual(session["status"], "disbanded")

        # Second disband attempt should be rejected
        r2, e2, msgs2 = self.history_service.disband_session("session-to-disband")
        self.assertEqual(r2, 0)
        self.assertEqual(e2, 1)

    def test_disband_collision_handling(self):
        cat_folder = self.dest_dir / "Photos"
        cat_folder.mkdir()
        dest_file = cat_folder / "img.png"
        dest_file.write_text("new image from destination")

        # Source already has a file with the same name
        orig_file = self.source_dir / "img.png"
        orig_file.write_text("existing file at source")

        result = OperationResult(
            session_id="collision-session",
            mode="By File Type",
            source_folder=str(self.source_dir),
            destination_folder=str(self.dest_dir),
            total_scanned=1,
            total_moved=1,
            created_folders=[str(cat_folder)],
            moves=[
                MoveRecord(
                    source=str(orig_file),
                    destination=str(dest_file),
                    timestamp=1000.0,
                    file_size=20,
                    category="Photos",
                    original_name="img.png",
                    final_name="img.png"
                )
            ]
        )

        self.history_service.record_session(result)
        restored, errors, _ = self.history_service.disband_session("collision-session")
        self.assertEqual(restored, 1)
        self.assertEqual(errors, 0)

        # Both files should exist safely
        self.assertTrue(orig_file.exists())
        self.assertEqual(orig_file.read_text(), "existing file at source")

        restored_file = self.source_dir / "img_restored_1.png"
        self.assertTrue(restored_file.exists())
        self.assertEqual(restored_file.read_text(), "new image from destination")


if __name__ == "__main__":
    unittest.main()
