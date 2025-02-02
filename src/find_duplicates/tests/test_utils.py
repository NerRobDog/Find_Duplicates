import os
import sys
import tempfile
import shutil
import unittest
from parameterized import parameterized
from find_duplicates.modules.utils import read_file, write_file, parse_arguments, human_readable_size


class TestReadWriteFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @parameterized.expand([
        ("normal_text", "Hello World"),
        ("empty_string", ""),
        ("unicode_text", "Привет мир"),
        ("special_chars", "Spécial Chåråctęrs: !@#$%^&*()")
    ])
    def test_write_and_read_file(self, name, content):
        file_path = os.path.join(self.test_dir, f"{name}.txt")
        write_file(file_path, content)
        read_content = read_file(file_path)
        self.assertEqual(read_content, content)

    def test_long_content(self):
        file_path = os.path.join(self.test_dir, "long.txt")
        content = "A" * 10000  # 10 000 символов
        write_file(file_path, content)
        self.assertEqual(read_file(file_path), content)

    def test_different_newlines(self):
        file_path = os.path.join(self.test_dir, "newlines.txt")
        content = "Line1\nLine2\r\nLine3\n"
        write_file(file_path, content)
        self.assertEqual(read_file(file_path), content)

    def test_read_nonexistent_file(self):
        file_path = os.path.join(self.test_dir, "nonexistent.txt")
        with self.assertRaises(Exception):
            read_file(file_path)

    def test_write_in_inaccessible_path(self):
        no_write_dir = os.path.join(self.test_dir, "no_write")
        os.mkdir(no_write_dir)
        os.chmod(no_write_dir, 0o444)  # Только чтение
        file_path = os.path.join(no_write_dir, "test.txt")
        with self.assertRaises(Exception):
            write_file(file_path, "Content")
        os.chmod(no_write_dir, 0o755)


class TestParseArguments(unittest.TestCase):
    def setUp(self):
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        sys.argv = self.original_argv

    def test_parse_arguments_valid(self):
        # Предполагается, что parse_arguments ожидает аргументы:
        # --directory, --exclude, --hash-type, --output, --log-level и т.д.
        sys.argv = ["prog", "--directory", "/tmp", "--exclude", "*.tmp",
                    "--hash-type", "sha256", "--output", "result.csv", "--log-level", "INFO"]
        args = parse_arguments()
        self.assertEqual(args.directory, "/tmp")
        self.assertEqual(args.exclude, ["*.tmp"])
        self.assertEqual(args.hash_type, "sha256")
        self.assertEqual(args.output, "result.csv")
        self.assertEqual(args.log_level, "INFO")

    def test_parse_arguments_missing_required(self):
        sys.argv = ["prog", "--exclude", "*.tmp"]
        with self.assertRaises(SystemExit):
            parse_arguments()

    def test_parse_arguments_invalid_flags(self):
        sys.argv = ["prog", "--unknown", "value"]
        with self.assertRaises(SystemExit):
            parse_arguments()


class TestHumanReadableSize(unittest.TestCase):
    @parameterized.expand([
        ("zero_bytes", 0, "0B"),
        ("kb_value", 2048, "2.00KB"),
        ("mb_value", 5 * 1024 * 1024, "5.00MB"),
        ("gb_value", 3 * 1024 * 1024 * 1024, "3.00GB"),
        ("very_large", 1234567890123, None)  # Здесь проверим формат (например, TB или PB)
    ])
    def test_human_readable_size(self, name, size, expected):
        result = human_readable_size(size)
        if expected is not None:
            self.assertEqual(result, expected)
        else:
            # Для очень большого значения проверяем, что результат – не пустая строка и содержит ожидаемый юнит
            self.assertTrue(isinstance(result, str) and len(result) > 0)
            self.assertRegex(result, r"^[\d\.]+(TB|PB)$")

    def test_boundary_cases(self):
        self.assertEqual(human_readable_size(1023), "1023.00B")
        self.assertEqual(human_readable_size(1024), "1.00KB")


if __name__ == "__main__":
    unittest.main()
