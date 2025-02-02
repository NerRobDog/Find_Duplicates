# Файл: tests/test_grouper.py
import os
import unittest
import tempfile
import shutil
from parameterized import parameterized
from find_duplicates.modules.grouper import group_files_by_size


def create_file(dir_path, name, content=""):
    """
    Утилита для создания текстового файла.
    Возвращает абсолютный путь к файлу.
    """
    full_path = os.path.join(dir_path, name)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full_path)

class TestGrouper(unittest.TestCase):
    """
    Тесты для функции group_files_by_size (UnitTest стиль).
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_group_same_size(self):
        """
        Два файла с одинаковым содержимым должны группироваться.
        """
        file1 = create_file(self.temp_dir, "f1.txt", "Hello")
        file2 = create_file(self.temp_dir, "f2.txt", "Hello")
        grouped = group_files_by_size([file1, file2])
        size = os.path.getsize(file1)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {file1, file2})

    def test_group_different_sizes(self):
        """
        Файлы разного размера не группируются – функция возвращает пустой словарь.
        """
        f1 = create_file(self.temp_dir, "a.txt", "abc")
        f2 = create_file(self.temp_dir, "b.txt", "abcd")
        grouped = group_files_by_size([f1, f2])
        self.assertEqual(grouped, {})

    def test_empty_input(self):
        """
        Передача пустого списка возвращает пустой словарь.
        """
        self.assertEqual(group_files_by_size([]), {})

    def test_nonexistent_ignored(self):
        """
        Несуществующие файлы игнорируются; если только один файл существует, группа не формируется.
        """
        exist = create_file(self.temp_dir, "exists.txt", "data")
        missing = os.path.join(self.temp_dir, "missing.txt")
        grouped = group_files_by_size([exist, missing])
        self.assertEqual(grouped, {})

    def test_directory_ignored(self):
        """
        Передача директории вместо файла возвращает пустой словарь.
        """
        d = os.path.join(self.temp_dir, "subdir")
        os.mkdir(d)
        grouped = group_files_by_size([d])
        self.assertEqual(grouped, {})

    def test_no_access_file(self):
        """
        Файл без прав доступа не учитывается.
        """
        file_path = create_file(self.temp_dir, "restricted.txt", "secret")
        os.chmod(file_path, 0o000)
        grouped = group_files_by_size([file_path])
        self.assertEqual(grouped, {})
        os.chmod(file_path, 0o644)

    def test_zero_size_file(self):
        """
        Файл размера 0 байт. Если только один файл, группа не формируется.
        """
        empty_file = create_file(self.temp_dir, "empty.txt", "")
        grouped = group_files_by_size([empty_file])
        self.assertEqual(grouped, {})

    def test_mixed_sizes(self):
        """
        Смешанный список: если несколько файлов имеют одинаковый размер, группа формируется.
        Если файл уникален по размеру, группа не создается.
        """
        a = create_file(self.temp_dir, "a.txt", "hello")
        b = create_file(self.temp_dir, "b.txt", "hello")
        c = create_file(self.temp_dir, "c.txt", "world!!!")
        grouped = group_files_by_size([a, b, c])
        size_hello = os.path.getsize(a)
        size_world = os.path.getsize(c)
        self.assertIn(size_hello, grouped)
        self.assertEqual(len(grouped[size_hello]), 2)
        self.assertNotIn(size_world, grouped)

    def test_same_size_in_different_dirs(self):
        """
        Файлы с одинаковым содержимым, но в разных директориях, должны группироваться.
        """
        d1 = os.path.join(self.temp_dir, "d1")
        d2 = os.path.join(self.temp_dir, "d2")
        os.mkdir(d1)
        os.mkdir(d2)
        f1 = create_file(d1, "file.txt", "data")
        f2 = create_file(d2, "file.txt", "data")
        grouped = group_files_by_size([f1, f2])
        size = os.path.getsize(f1)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {f1, f2})

    def test_nonascii_filenames(self):
        """
        Файл с non‑ASCII именем – если только один, группа не формируется.
        """
        f = create_file(self.temp_dir, "файл.txt", "unicode data")
        grouped = group_files_by_size([f])
        self.assertEqual(grouped, {})

    def test_spaces_in_filename(self):
        """
        Файл с пробелами в имени – если только один, группа не формируется.
        """
        f = create_file(self.temp_dir, "my file.txt", "some data")
        grouped = group_files_by_size([f])
        self.assertEqual(grouped, {})

    @parameterized.expand([
        ("small_count", 100),
        ("bigger_test", 150),
    ])
    def test_large_number_of_files(self, name, count):
        """
        Масштабируемость: создаём большое число файлов с одинаковым содержимым.
        """
        files = []
        for i in range(count):
            f = create_file(self.temp_dir, f"file_{i}.txt", "same content")
            files.append(f)
        grouped = group_files_by_size(files)
        size = os.path.getsize(files[0])
        self.assertIn(size, grouped)
        self.assertEqual(len(grouped[size]), count)

    @unittest.skipIf(not hasattr(os, "symlink"), "Symlinks not supported")
    def test_symlink_handling(self):
        """
        Проверяем обработку симлинков.
        """
        target = create_file(self.temp_dir, "target.txt", "symlink test")
        # Удаляем существующий файл для создания симлинка
        link = os.path.join(self.temp_dir, "link.txt")
        if os.path.exists(link):
            os.remove(link)
        os.symlink(target, link)
        grouped = group_files_by_size([target, link])
        size = os.path.getsize(target)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {target, link})

    def test_duplicate_names_in_diff_folders(self):
        """
        Файлы с одинаковым именем в разных папках с одинаковым содержимым должны группироваться.
        """
        d1 = os.path.join(self.temp_dir, "folder1")
        d2 = os.path.join(self.temp_dir, "folder2")
        os.mkdir(d1)
        os.mkdir(d2)
        f1 = create_file(d1, "common.txt", "duplicate")
        f2 = create_file(d2, "common.txt", "duplicate")
        grouped = group_files_by_size([f1, f2])
        size = os.path.getsize(f1)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {f1, f2})

    def test_return_type_and_keys(self):
        """
        Проверяем, что функция возвращает словарь, где ключи — int, а значения — список строк.
        """
        f = create_file(self.temp_dir, "check.txt", "content")
        grouped = group_files_by_size([f])
        self.assertIsInstance(grouped, dict)
        for key, val in grouped.items():
            self.assertIsInstance(key, int)
            self.assertIsInstance(val, list)
            for item in val:
                self.assertIsInstance(item, str)

if __name__ == "__main__":
    unittest.main()