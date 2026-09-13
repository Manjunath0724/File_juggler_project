"""Tests for the FileClassifier engine."""
import time
import unittest
from datetime import datetime, timedelta

from src.models.file_item import FileItem
from src.models.organization_rule import OrganizationConfig, OrganizationMode
from src.core.classifier import FileClassifier


class TestFileClassifier(unittest.TestCase):

    def setUp(self):
        self.config = OrganizationConfig(mode=OrganizationMode.BY_TYPE)
        self.classifier = FileClassifier(self.config)

    def test_file_type_categories(self):
        test_cases = [
            ("photo.jpg", "Photos & Images"),
            ("banner.PNG", "Photos & Images"),
            ("doc.pdf", "PDF Documents"),
            ("notes.docx", "Word Documents"),
            ("sheet.xlsx", "Excel & Spreadsheets"),
            ("deck.pptx", "PowerPoint Presentations"),
            ("memo.txt", "Text & Notes"),
            ("icon.svg", "Vector Graphics"),
            ("anim.gif", "GIFs & Animations"),
            ("raw_pic.dng", "RAW Camera Files"),
            ("clip.mp4", "Videos"),
            ("track.mp3", "Audio"),
            ("backup.zip", "Archives"),
            ("installer.exe", "Applications"),
            ("main.py", "Code"),
            ("style.css", "Code"),
            ("unknown_file", "Other"),
            ("custom.xyz123", "Other"),
        ]

        for filename, expected_category in test_cases:
            item = FileItem(
                name=filename,
                full_path=f"C:/mock/{filename}",
                extension=f".{filename.split('.')[-1]}" if "." in filename else "",
                size_bytes=1024,
                modified_time=time.time(),
            )
            cat, _ = self.classifier.classify_by_type(item)
            self.assertEqual(cat, expected_category, f"Failed for {filename}: got {cat}, expected {expected_category}")

    def test_date_classification(self):
        now = datetime.now()
        item_today = FileItem(
            name="today.txt",
            full_path="C:/mock/today.txt",
            extension=".txt",
            size_bytes=100,
            modified_time=now.timestamp(),
        )
        cat_today, _ = self.classifier.classify_by_date(item_today)
        self.assertEqual(cat_today, "Today")

        item_yesterday = FileItem(
            name="yesterday.txt",
            full_path="C:/mock/yesterday.txt",
            extension=".txt",
            size_bytes=100,
            modified_time=(now - timedelta(days=1)).timestamp(),
        )
        cat_yesterday, _ = self.classifier.classify_by_date(item_yesterday)
        self.assertEqual(cat_yesterday, "Yesterday")

    def test_combined_classification(self):
        self.config.mode = OrganizationMode.COMBINED
        self.config.combined_pattern = "type_then_size"
        classifier = FileClassifier(self.config)

        item = FileItem(
            name="huge_photo.jpg",
            full_path="C:/mock/huge_photo.jpg",
            extension=".jpg",
            size_bytes=2 * 1024 * 1024 * 1024,  # 2 GB
            modified_time=time.time(),
        )
        cat, _ = classifier.classify_combined(item)
        self.assertEqual(cat, "Photos & Images/Huge (>1 GB)")


if __name__ == "__main__":
    unittest.main()
