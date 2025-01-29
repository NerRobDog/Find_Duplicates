import unittest


class TestOutput(unittest.TestCase):
    def test_print_results(self):
        """Tests the print_results function."""
        # Arrange
        results = {'key': 'value'}

        # Act
        print_results(results)


if __name__ == '__main__':
    unittest.main()
