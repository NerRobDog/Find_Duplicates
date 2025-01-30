import unittest
from pathlib import Path
from ..modules.scanner import scan_directory

class TestScanner(unittest.TestCase):
    def test_scan_files(self):
        """Tests the scan_files function."""
        # Arrange
        directory_path = str(Path(__file__).parent / 'test_data' / 'sample_dir')
        expected_files = ['file1.txt', 'file2.txt']

        # Act
        result = scan_directory(directory_path)

        # Assert
        self.assertEqual(sorted(result), sorted(expected_files))

    def test_scan_exclude_pattern(self):
        """Tests the scan_files function with an exclude pattern."""
        # Arrange
        directory_path = str(Path(__file__).parent / 'test_data' / 'sample_dir')
        expected_files = []
        exclude_patterns = ['*.txt']

        # Act
        result = scan_directory(directory_path, exclude=exclude_patterns)

        # Assert
        self.assertEqual(sorted(result), sorted(expected_files))

    def test_scan_include_hidden(self):
        """Tests the scan_files function with include_hidden=True."""
        # Arrange
        directory_path = str(Path(__file__).parent / 'test_data' / 'sample_dir_with_hidden')
        expected_files = ['file1.txt', '.hidden_file.txt', '.hidden_dir/hidden_in_dir.txt']
        exclude_patterns = []

        # Act
        result = scan_directory(directory_path, exclude=exclude_patterns, include_hidden=True)

        # Assert
        self.assertEqual(sorted(result), sorted(expected_files))

    def test_scan_files_with_cyrillic_and_spaces(self):
        """Tests the scan_files function with Cyrillic and spaces in filenames."""
        # Arrange
        directory_path = str(Path(__file__).parent / 'test_data' / 'sample_dir_with_special_chars')
        expected_files = ['file1.txt', 'файл с пробелом.txt', 'файл.txt', 'file with spaces.txt']
        exclude_patterns = []

        # Act
        result = scan_directory(directory_path, exclude=exclude_patterns)

        # Assert
        self.assertEqual(sorted(result), sorted(expected_files))

if __name__ == '__main__':
    unittest.main()
