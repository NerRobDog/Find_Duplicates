import unittest


class TestHasher(unittest.TestCase):
    def test_calculate_hash(self):
        """Tests the calculate_hash function."""
        # Arrange
        file_path = '/path/to/file.txt'
        expected_hash = 'expected_hash_value'

        # Act
        result = calculate_hash(file_path)

        # Assert
        self.assertEqual(result, expected_hash)


if __name__ == '__main__':
    unittest.main()
