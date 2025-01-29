import unittest


class TestScanner(unittest.TestCase):
    def test_scan_files(self):
        """Tests the scan_files function."""
        # Arrange
        directory_path = '/path/to/directory'
        expected_files = ['file1.txt', 'file2.txt']

        # Act
        result = scan_files(directory_path)

        # Assert
        self.assertEqual(result, expected_files)


if __name__ == '__main__':
    unittest.main()
