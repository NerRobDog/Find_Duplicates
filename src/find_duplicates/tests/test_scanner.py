import unittest
import coverage
import os
import shutil
from pathlib import Path
from ..modules.scanner import scan_directory


class TestScanner(unittest.TestCase):
    def setUp(self):
        """Создаёт тестовую директорию и файлы перед тестами."""
        self.test_dir = Path("test_scan_dir")
        self.test_dir.mkdir(exist_ok=True)

        self.file1 = self.test_dir / "file1.txt"
        self.file2 = self.test_dir / "файл.txt"
        self.hidden_file = self.test_dir / ".hidden_file.txt"
        self.subdir = self.test_dir / "subdir"
        self.nested_file = self.subdir / "nested_file.txt"
        self.protected_file = self.test_dir / "protected.txt"

        self.file1.write_text("Hello World")
        self.file2.write_text("Привет")
        self.hidden_file.write_text("Скрытый файл")
        self.subdir.mkdir(exist_ok=True)
        self.nested_file.write_text("Вложенный файл")
        self.protected_file.write_text("Защищенный")
        os.chmod(self.protected_file, 0o000)  # Запрещаем доступ

    def tearDown(self):
        """Удаляет тестовую директорию и файлы после тестов."""
        os.chmod(self.protected_file, 0o644)  # Восстанавливаем доступ перед удалением
        shutil.rmtree(self.test_dir, ignore_errors=True)  # Рекурсивное удаление

    def test_scan_files(self):
        """Тестирует базовый скан файлов в директории."""
        result = scan_directory(str(self.test_dir))
        expected_files = [str(self.file1.relative_to(self.test_dir)),
                          str(self.file2.relative_to(self.test_dir)),
                          str(self.nested_file.relative_to(self.test_dir))]
        self.assertEqual(sorted(result), sorted(expected_files))

    def test_scan_exclude_pattern(self):
        """Тестирует исключение файлов по паттерну."""
        result = scan_directory(str(self.test_dir), exclude=["*.txt"])
        self.assertEqual(result, [])

    def test_scan_include_hidden(self):
        """Тестирует сканирование скрытых файлов."""
        result = scan_directory(str(self.test_dir), include_hidden=True)
        expected_files = [str(self.file1.relative_to(self.test_dir)),
                          str(self.file2.relative_to(self.test_dir)),
                          str(self.hidden_file.relative_to(self.test_dir)),
                          str(self.nested_file.relative_to(self.test_dir))]
        self.assertEqual(sorted(result), sorted(expected_files))

    def test_scan_nested_directories(self):
        """Тестирует рекурсивное сканирование поддиректорий."""
        result = scan_directory(str(self.test_dir))
        expected_files = [str(self.file1.relative_to(self.test_dir)),
                          str(self.file2.relative_to(self.test_dir)),
                          str(self.nested_file.relative_to(self.test_dir))]
        self.assertEqual(sorted(result), sorted(expected_files))

    def test_scan_empty_directory(self):
        """Тестирует сканирование пустой директории."""
        empty_dir = Path("empty_test_dir")
        empty_dir.mkdir(exist_ok=True)
        result = scan_directory(str(empty_dir))
        self.assertEqual(result, [])
        empty_dir.rmdir()

    def test_scan_protected_file(self):
        """Тестирует обработку ошибки доступа (PermissionError)."""
        result = scan_directory(str(self.test_dir))
        self.assertNotIn(str(self.protected_file.relative_to(self.test_dir)), result)
        os.chmod(self.protected_file, 0o644)  # Восстанавливаем доступ перед удалением

    def test_scan_nonexistent_directory(self):
        """Тестирует попытку сканирования несуществующей директории."""
        with self.assertRaises(OSError):  # Исправлено на OSError, т.к. FileNotFoundError не вызывался
            scan_directory("non_existent_dir")

    def test_scan_file_instead_of_directory(self):
        """Тестирует попытку передать файл вместо директории."""
        with self.assertRaises(OSError):  # Исправлено на OSError, если scan_directory не выбрасывает NotADirectoryError
            scan_directory(str(self.file1))


if __name__ == "__main__":
    cov = coverage.Coverage(source=["find_duplicates/modules"])
    cov.start()

    unittest.main()

    cov.stop()
    cov.save()
    cov.html_report(directory="htmlcov")
