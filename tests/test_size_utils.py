"""Tests for size formatting and classification utilities."""
import unittest
from src.utils.size_utils import format_size, classify_size, DEFAULT_SIZE_THRESHOLDS


class TestSizeUtils(unittest.TestCase):

    def test_format_size(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024 * 5), "5.0 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024 * 2), "2.0 GB")

    def test_classify_size(self):
        # 500 KB -> Tiny
        self.assertEqual(classify_size(500 * 1024), "Tiny (<1 MB)")
        # 5 MB -> Small
        self.assertEqual(classify_size(5 * 1024 * 1024), "Small (1-10 MB)")
        # 50 MB -> Medium
        self.assertEqual(classify_size(50 * 1024 * 1024), "Medium (10-100 MB)")
        # 500 MB -> Large
        self.assertEqual(classify_size(500 * 1024 * 1024), "Large (100 MB - 1 GB)")
        # 2 GB -> Huge
        self.assertEqual(classify_size(2 * 1024 * 1024 * 1024), "Huge (>1 GB)")


if __name__ == "__main__":
    unittest.main()
