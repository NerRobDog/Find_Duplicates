import os
import tempfile
import shutil
import unittest
from parameterized import parameterized
from find_duplicates.modules.scanner import scan_directory, is_excluded


class TestScannerParameterized(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Базовые файлы: обычный и скрытый
        with open(os.path.join(self.test_dir, "file.txt"), "w", encoding="utf-8") as f:
            f.write("Content")
        with open(os.path.join(self.test_dir, ".hidden.txt"), "w", encoding="utf-8") as f:
            f.write("Hidden")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @parameterized.expand([
        ("without_hidden", False, ["file.txt"]),
        ("with_hidden", True, ["file.txt", ".hidden.txt"]),
    ])
    def test_include_hidden(self, name, include_hidden, expected):
        result = scan_directory(self.test_dir, include_hidden=include_hidden)
        self.assertEqual(sorted(result), sorted(expected))

    def test_nested_directories(self):
        # Создаём вложенную директорию с файлом
        nested_dir = os.path.join(self.test_dir, "subdir")
        os.mkdir(nested_dir)
        nested_file = os.path.join(nested_dir, "nested.txt")
        with open(nested_file, "w") as f:
            f.write("Nested")
        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertIn("subdir/nested.txt", result)

    def test_symlink_handling(self):
        # Если ОС поддерживает симлинки
        if hasattr(os, "symlink"):
            target_file = os.path.join(self.test_dir, "file.txt")
            symlink_path = os.path.join(self.test_dir, "link.txt")
            os.symlink(target_file, symlink_path)
            # При follow_symlinks=False симлинк не должен попадать в результат
            result_no_follow = scan_directory(self.test_dir, include_hidden=True, follow_symlinks=False)
            self.assertNotIn("link.txt", result_no_follow)
            # При follow_symlinks=True симлинк должен включаться
            result_follow = scan_directory(self.test_dir, include_hidden=True, follow_symlinks=True)
            self.assertIn("link.txt", result_follow)
        else:
            self.skipTest("Симлинки не поддерживаются в этой ОС")

    def test_path_not_directory(self):
        # Передаём файл вместо директории – ожидается OSError
        file_path = os.path.join(self.test_dir, "file.txt")
        with self.assertRaises(OSError):
            scan_directory(file_path)

    def test_files_without_permission(self):
        # Создаём файл и убираем права на чтение
        no_read_file = os.path.join(self.test_dir, "noread.txt")
        with open(no_read_file, "w") as f:
            f.write("Secret")
        os.chmod(no_read_file, 0o000)
        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertNotIn("noread.txt", result)
        os.chmod(no_read_file, 0o644)

    @parameterized.expand([
        ("exclude_all_txt", ["*.txt"], []),
        ("exclude_hidden", [".*"], ["file.txt"]),
    ])
    def test_exclude_patterns(self, name, exclude_patterns, expected_files):
        # Добавляем ещё один файл, чтобы проверить работу шаблонов
        extra_file = os.path.join(self.test_dir, "keep.log")
        with open(extra_file, "w") as f:
            f.write("Log data")
        result = scan_directory(self.test_dir, exclude=exclude_patterns, include_hidden=True)
        # Проверяем, что ни один файл не удовлетворяет исключающему шаблону
        for f in result:
            for pattern in exclude_patterns:
                self.assertFalse(is_excluded(f, [pattern]))
        # Проверяем, что ожидаемые файлы присутствуют
        for exp in expected_files:
            self.assertIn(exp, result)

    def test_unicode_filenames(self):
        # Файл с non-ASCII именем
        unicode_file = os.path.join(self.test_dir, "файл.txt")
        with open(unicode_file, "w", encoding="utf-8") as f:
            f.write("Unicode")
        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertIn("файл.txt", result)

    def test_spaces_in_filename(self):
        # Файл с пробелами в имени
        spaced_file = os.path.join(self.test_dir, "file with spaces.txt")
        with open(spaced_file, "w") as f:
            f.write("Spaces")
        result = scan_directory(self.test_dir, include_hidden=True)
        self.assertIn("file with spaces.txt", result)

    def test_nonexistent_directory(self):
        # Передаём несуществующую директорию
        non_exist_dir = os.path.join(self.test_dir, "nonexistent")
        with self.assertRaises(OSError):
            scan_directory(non_exist_dir)

    def test_deep_nested_directories(self):
        # Создаём цепочку вложенных директорий
        deep_dir = self.test_dir
        for i in range(5):
            deep_dir = os.path.join(deep_dir, f"nested{i}")
            os.mkdir(deep_dir)
        deep_file = os.path.join(deep_dir, "deep.txt")
        with open(deep_file, "w") as f:
            f.write("Deep content")
        result = scan_directory(self.test_dir, include_hidden=True)
        expected_rel = os.path.relpath(deep_file, os.path.abspath(self.test_dir))
        self.assertIn(expected_rel, result)

    def test_multiple_exclude_patterns(self):
        # Создаём файлы с различными расширениями
        for fname, content in [("a.txt", "A"), ("b.log", "B"), ("c.tmp", "C")]:
            with open(os.path.join(self.test_dir, fname), "w") as f:
                f.write(content)
        # Исключаем файлы с расширениями .txt и .tmp
        result = scan_directory(self.test_dir, exclude=["*.txt", "*.tmp"], include_hidden=True)
        self.assertNotIn("a.txt", result)
        self.assertNotIn("c.tmp", result)
        self.assertIn("b.log", result)

    def test_relative_paths(self):
        # Проверяем, что возвращаемые пути относительные относительно базовой директории
        file_path = os.path.join(self.test_dir, "relative.txt")
        with open(file_path, "w") as f:
            f.write("Relative")
        result = scan_directory(self.test_dir, include_hidden=True)
        for path in result:
            self.assertFalse(os.path.isabs(path))

    def test_empty_directory(self):
        # Тестирование пустой директории
        empty_dir = os.path.join(self.test_dir, "empty")
        os.mkdir(empty_dir)
        result = scan_directory(empty_dir, include_hidden=True)
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
