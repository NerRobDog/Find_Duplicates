import os
import unittest
import tempfile
import shutil
from parameterized import parameterized
from find_duplicates.modules.scanner import scan_directory, is_excluded


class TestScannerBase(unittest.TestCase):
    """
    Базовые тесты для функции scan_directory (UnitTest стиль).
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_directory_with_normal_file(self):
        """
        Директория с обычными файлами.
        """
        file_path = os.path.join(self.test_dir, "file.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Normal")

        result = scan_directory(self.test_dir)
        basenames = [os.path.basename(p) for p in result]
        self.assertIn("file.txt", basenames)

    def test_include_hidden(self):
        """
        Проверка include_hidden=True.
        """
        hidden_file = os.path.join(self.test_dir, ".hidden.txt")
        with open(hidden_file, "w", encoding="utf-8") as f:
            f.write("Hidden")

        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertIn(".hidden.txt", [os.path.basename(p) for p in result])

    def test_exclude_hidden(self):
        """
        Проверка include_hidden=False.
        """
        hidden_file = os.path.join(self.test_dir, ".hidden.txt")
        with open(hidden_file, "w", encoding="utf-8") as f:
            f.write("Hidden")

        result = scan_directory(self.test_dir, include_hidden=False)
        self.assertNotIn(".hidden.txt", [os.path.basename(p) for p in result])

    def test_nonexistent_directory(self):
        """
        Не существующая директория => OSError.
        """
        with self.assertRaises(OSError):
            scan_directory(os.path.join(self.test_dir, "no_dir"))

    def test_is_excluded(self):
        """
        Тест для функции is_excluded.
        """
        self.assertTrue(is_excluded("file.log", ["*.log"]))
        self.assertFalse(is_excluded("file.txt", ["*.log"]))

    def test_empty_directory(self):
        """
        Пустая директория => пустой список.
        """
        result = scan_directory(self.test_dir)
        self.assertEqual(result, [])

    @parameterized.expand([
        ("locked_dir", True, []),
        ("locked_dir_raise", False, PermissionError)  # Ожидаем исключение
    ])
    def test_directory_with_no_access(self, name, skip_inacc, expected):
        """
        Директория без прав на чтение: если skip_inaccessible=True, пропускается;
        Иначе вызывается ошибка.
        """
        locked = os.path.join(self.test_dir, "locked")
        os.mkdir(locked)
        os.chmod(locked, 0o000)

        if isinstance(expected, list):
            result = scan_directory(self.test_dir, skip_inaccessible=skip_inacc)
            self.assertEqual(result, [], "Ожидаем, что недоступная директория будет пропущена")
        else:
            with self.assertRaises(expected):
                scan_directory(self.test_dir, skip_inaccessible=skip_inacc)
        os.chmod(locked, 0o755)

    def test_exclude_pattern(self):
        """
        Исключение по шаблонам.
        """
        file_log = os.path.join(self.test_dir, "file.log")
        with open(file_log, "w", encoding="utf-8") as f:
            f.write("Log data")
        file_txt = os.path.join(self.test_dir, "file.txt")
        with open(file_txt, "w", encoding="utf-8") as f:
            f.write("Text")

        result = scan_directory(self.test_dir, exclude=["*.log"])
        basenames = [os.path.basename(p) for p in result]
        self.assertNotIn("file.log", basenames)
        self.assertIn("file.txt", basenames)

    def test_unicode_filenames(self):
        """
        Файл с unicode-именем.
        """
        uni_file = os.path.join(self.test_dir, "файл.txt")
        with open(uni_file, "w", encoding="utf-8") as f:
            f.write("Данные")
        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertIn("файл.txt", [os.path.basename(p) for p in result])

    def test_spaces_in_filename(self):
        """
        Файл с пробелами в имени.
        """
        spaced = os.path.join(self.test_dir, "my file.txt")
        with open(spaced, "w", encoding="utf-8") as f:
            f.write("Spaces")

        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertIn("my file.txt", [os.path.basename(p) for p in result])

    def test_nested_subdirectories(self):
        """
        Проверка рекурсивного обхода.
        """
        sub = os.path.join(self.test_dir, "sub")
        os.mkdir(sub)
        nested_file = os.path.join(sub, "nested.txt")
        with open(nested_file, "w", encoding="utf-8") as f:
            f.write("Nested")

        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertTrue(any("nested.txt" in path for path in result))

    @unittest.skipIf(not hasattr(os, "symlink"), "Симлинки не поддерживаются")
    def test_symlink_handling(self):
        """
        Тестируем обработку симлинков (при follow_symlinks=False).
        """
        target_file = os.path.join(self.test_dir, "target.txt")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("Data")

        link_path = os.path.join(self.test_dir, "link.txt")
        os.symlink(target_file, link_path)

        result = scan_directory(self.test_dir, include_hidden=True)
        # При follow_symlinks=False link не должен включаться как отдельный файл
        self.assertNotIn("link.txt", [os.path.basename(p) for p in result])


if __name__ == "__main__":
    unittest.main()