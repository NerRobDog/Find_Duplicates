# Файл: tests/test_utils.py
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch
from parameterized import parameterized

from find_duplicates.modules.utils import (
    normalize_path,
    get_file_info,
    check_symlink_support,
    validate_directory,
    check_file_exists,
    check_file_readable,
    parse_arguments,
    handle_error,
    human_readable_size
)


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_normalize_path_basic(self):
        d = os.path.join(self.test_dir, "sub", "dir")
        os.makedirs(d)
        rel_path = os.path.join("sub", "dir", "..", "dir")
        expected = os.path.normpath(os.path.abspath(d))
        result = normalize_path(os.path.join(self.test_dir, rel_path))
        self.assertEqual(result, expected)

    def test_get_file_info_existing_file(self):
        fpath = os.path.join(self.test_dir, "file.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Hello")
        info = get_file_info(fpath)
        self.assertEqual(info["path"], os.path.normpath(os.path.abspath(fpath)))
        self.assertEqual(info["size"], os.path.getsize(fpath))

    def test_get_file_info_nonexistent(self):
        missing = os.path.join(self.test_dir, "missing.txt")
        info = get_file_info(missing)
        self.assertIsNone(info["size"])
        self.assertEqual(info["path"], os.path.normpath(os.path.abspath(missing)))

    def test_check_symlink_support(self):
        result = check_symlink_support()
        self.assertIsInstance(result, bool)

    def test_validate_directory_valid(self):
        self.assertTrue(validate_directory(self.test_dir))

    def test_validate_directory_nonexistent(self):
        non_exist = os.path.join(self.test_dir, "no_dir")
        with self.assertRaises(NotADirectoryError):
            validate_directory(non_exist)

    def test_validate_directory_no_permission(self):
        locked = os.path.join(self.test_dir, "locked")
        os.mkdir(locked)
        os.chmod(locked, 0o000)
        try:
            with self.assertRaises(PermissionError):
                validate_directory(locked)
        finally:
            os.chmod(locked, 0o700)

    def test_check_file_exists_valid(self):
        fpath = os.path.join(self.test_dir, "file.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Content")
        check_file_exists(fpath)  # Не должно выбрасывать исключения

    def test_check_file_exists_missing(self):
        missing = os.path.join(self.test_dir, "missing.txt")
        with self.assertRaises(FileNotFoundError):
            check_file_exists(missing)

    def test_check_file_readable_ok(self):
        fpath = os.path.join(self.test_dir, "readable.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Hello")
        check_file_readable(fpath)

    def test_check_file_readable_no_access(self):
        fpath = os.path.join(self.test_dir, "no_access.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("Secret")
        os.chmod(fpath, 0o000)
        try:
            with self.assertRaises(PermissionError):
                check_file_readable(fpath)
        finally:
            os.chmod(fpath, 0o644)

    @parameterized.expand([
        (0, "0B"),
        (999, "999.00B"),
        (1024, "1.00KB"),
        (2048, "2.00KB"),
        (5 * 1024 * 1024, "5.00MB"),
        (3 * 1024 * 1024 * 1024, "3.00GB"),
        (999999999999, None),
    ])
    def test_human_readable_size(self, size, expected):
        if expected is not None:
            self.assertEqual(human_readable_size(size), expected)
        else:
            res = human_readable_size(size)
            self.assertTrue(len(res) > 0)
            self.assertTrue(
                res.endswith("GB") or res.endswith("TB") or res.endswith("PB"),
                f"Ожидали GB, TB или PB, получили {res}"
            )

    def test_handle_error(self):
        e = ValueError("Sample error")
        msg = handle_error(e, context="Testing error")
        self.assertIn("Testing error", msg)
        self.assertIn("Sample error", msg)

    def test_parse_arguments_valid(self):
        test_args = [
            "prog", "--directory", "/tmp", "--exclude", "*.tmp",
            "--hash-type", "md5", "--output", "results.csv",
            "--log-level", "DEBUG", "--skip-inaccessible"
        ]
        with patch.object(sys, "argv", test_args):
            args = parse_arguments()
            self.assertEqual(args.directory, "/tmp")
            self.assertEqual(args.exclude, ["*.tmp"])
            self.assertEqual(args.hash_type, "md5")
            self.assertEqual(args.output, "results.csv")
            self.assertEqual(args.log_level, "DEBUG")
            self.assertTrue(args.skip_inaccessible)

    def test_parse_arguments_missing_required(self):
        test_args = ["prog", "--exclude", "*.tmp"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()

    def test_parse_arguments_invalid_flags(self):
        test_args = ["prog", "--unknown", "value"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()

if __name__ == "__main__":
    unittest.main()