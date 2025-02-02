import os
import tempfile
import shutil
import unittest
from parameterized import parameterized
from find_duplicates.modules.grouper import group_files_by_size

class TestGrouper(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # 1. Группировка файлов с одинаковым и разными размерами
    @parameterized.expand([
        # Кейсы: два файла с одинаковым содержимым (одинаковый размер)
        ("same_size", "Hello", "Hello"),
        # Кейсы: два файла с разным содержимым (разные размеры)
        ("different_size", "Hello", "World!")
    ])
    def test_grouping_same_and_different(self, name, content1, content2):
        file1 = os.path.join(self.test_dir, f"file1_{name}.txt")
        file2 = os.path.join(self.test_dir, f"file2_{name}.txt")
        with open(file1, "w") as f:
            f.write(content1)
        with open(file2, "w") as f:
            f.write(content2)
        grouped = group_files_by_size([file1, file2])
        if content1 == content2:
            expected_size = os.path.getsize(file1)
            self.assertIn(expected_size, grouped)
            self.assertEqual(len(grouped[expected_size]), 2)
        else:
            size1 = os.path.getsize(file1)
            size2 = os.path.getsize(file2)
            self.assertIn(size1, grouped)
            self.assertIn(size2, grouped)
            self.assertEqual(len(grouped[size1]), 1)
            self.assertEqual(len(grouped[size2]), 1)

    # 2. Передача пустого списка
    def test_empty_list(self):
        self.assertEqual(group_files_by_size([]), {})

    # 3. Файлы, которых не существует (должны быть проигнорированы)
    def test_nonexistent_files(self):
        file1 = os.path.join(self.test_dir, "file.txt")
        with open(file1, "w") as f:
            f.write("data")
        non_exist = os.path.join(self.test_dir, "missing.txt")
        grouped = group_files_by_size([file1, non_exist])
        size = os.path.getsize(file1)
        self.assertIn(size, grouped)
        self.assertEqual(grouped[size], [file1])

    # 4. Передача директорий вместо файлов (директории должны быть проигнорированы)
    def test_directory_instead_of_file(self):
        dir_path = os.path.join(self.test_dir, "subdir")
        os.mkdir(dir_path)
        grouped = group_files_by_size([dir_path])
        self.assertEqual(grouped, {})

    # 5. Файлы без прав доступа (должны быть проигнорированы)
    def test_file_without_permission(self):
        file_path = os.path.join(self.test_dir, "no_access.txt")
        with open(file_path, "w") as f:
            f.write("restricted")
        os.chmod(file_path, 0o000)
        grouped = group_files_by_size([file_path])
        self.assertEqual(grouped, {})
        os.chmod(file_path, 0o644)

    # 6. Группировка бинарных файлов
    def test_grouping_binary_file(self):
        file_path = os.path.join(self.test_dir, "binary.bin")
        data = os.urandom(256)
        with open(file_path, "wb") as f:
            f.write(data)
        grouped = group_files_by_size([file_path])
        size = os.path.getsize(file_path)
        self.assertIn(size, grouped)
        self.assertEqual(grouped[size], [file_path])

    # 7. Группировка текстовых файлов
    def test_grouping_text_file(self):
        file_path = os.path.join(self.test_dir, "text.txt")
        content = "Some text data"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        grouped = group_files_by_size([file_path])
        size = os.path.getsize(file_path)
        self.assertIn(size, grouped)
        self.assertEqual(grouped[size], [file_path])

    # 8. Файлы размера 0
    def test_file_size_zero(self):
        file_path = os.path.join(self.test_dir, "empty.txt")
        open(file_path, "w").close()
        grouped = group_files_by_size([file_path])
        self.assertIn(0, grouped)
        self.assertEqual(grouped[0], [file_path])

    # 9. Смешанный список файлов (одни файлы с одинаковым размером, другие – нет)
    def test_mixed_list(self):
        file1 = os.path.join(self.test_dir, "a.txt")
        file2 = os.path.join(self.test_dir, "b.txt")
        file3 = os.path.join(self.test_dir, "c.txt")
        with open(file1, "w") as f:
            f.write("same")
        with open(file2, "w") as f:
            f.write("same")
        with open(file3, "w") as f:
            f.write("different")
        grouped = group_files_by_size([file1, file2, file3])
        size_same = os.path.getsize(file1)
        size_diff = os.path.getsize(file3)
        self.assertIn(size_same, grouped)
        self.assertEqual(len(grouped[size_same]), 2)
        self.assertIn(size_diff, grouped)
        self.assertEqual(len(grouped[size_diff]), 1)

    # 10. Файлы с одинаковым размером, но в разных директориях
    def test_same_size_different_directories(self):
        subdir1 = os.path.join(self.test_dir, "dir1")
        subdir2 = os.path.join(self.test_dir, "dir2")
        os.mkdir(subdir1)
        os.mkdir(subdir2)
        file1 = os.path.join(subdir1, "file.txt")
        file2 = os.path.join(subdir2, "file.txt")
        content = "identical"
        with open(file1, "w") as f:
            f.write(content)
        with open(file2, "w") as f:
            f.write(content)
        grouped = group_files_by_size([file1, file2])
        size = os.path.getsize(file1)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {file1, file2})

    # 11. Файлы с non‑ASCII именами
    def test_nonascii_filenames(self):
        file_path = os.path.join(self.test_dir, "файл.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("data")
        grouped = group_files_by_size([file_path])
        size = os.path.getsize(file_path)
        self.assertIn(size, grouped)
        self.assertEqual(grouped[size], [file_path])

    # 12. Файлы с пробелами в имени
    def test_spaces_in_filename(self):
        file_path = os.path.join(self.test_dir, "file with spaces.txt")
        with open(file_path, "w") as f:
            f.write("content")
        grouped = group_files_by_size([file_path])
        size = os.path.getsize(file_path)
        self.assertIn(size, grouped)
        self.assertEqual(grouped[size], [file_path])

    # 13. Большое число файлов (проверка масштабируемости)
    def test_large_number_of_files(self):
        num_files = 50  # для демонстрации; можно увеличить
        file_paths = []
        for i in range(num_files):
            path = os.path.join(self.test_dir, f"file_{i}.txt")
            with open(path, "w") as f:
                f.write("scalable")
            file_paths.append(path)
        grouped = group_files_by_size(file_paths)
        size = os.path.getsize(file_paths[0])
        self.assertIn(size, grouped)
        self.assertEqual(len(grouped[size]), num_files)

    # 14. Файлы-симлинки (если обрабатываются)
    def test_file_symlink(self):
        if not hasattr(os, "symlink"):
            self.skipTest("Симлинки не поддерживаются")
        target = os.path.join(self.test_dir, "target.txt")
        with open(target, "w") as f:
            f.write("symlink test")
        symlink_path = os.path.join(self.test_dir, "link.txt")
        os.symlink(target, symlink_path)
        grouped = group_files_by_size([target, symlink_path])
        size = os.path.getsize(target)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {target, symlink_path})

    # 15. Повторяющиеся имена в разных папках
    def test_duplicate_names_in_different_folders(self):
        dir1 = os.path.join(self.test_dir, "d1")
        dir2 = os.path.join(self.test_dir, "d2")
        os.mkdir(dir1)
        os.mkdir(dir2)
        file_name = "common.txt"
        file1 = os.path.join(dir1, file_name)
        file2 = os.path.join(dir2, file_name)
        with open(file1, "w") as f:
            f.write("duplicate")
        with open(file2, "w") as f:
            f.write("duplicate")
        grouped = group_files_by_size([file1, file2])
        size = os.path.getsize(file1)
        self.assertIn(size, grouped)
        self.assertEqual(set(grouped[size]), {file1, file2})

    # 16. Проверка, что функция возвращает словарь и корректность типов ключей и значений
    def test_return_type_and_key_value_types(self):
        file1 = os.path.join(self.test_dir, "a.txt")
        file2 = os.path.join(self.test_dir, "b.txt")
        with open(file1, "w") as f:
            f.write("content")
        with open(file2, "w") as f:
            f.write("different")
        grouped = group_files_by_size([file1, file2])
        self.assertIsInstance(grouped, dict)
        for key, value in grouped.items():
            self.assertIsInstance(key, int)
            self.assertIsInstance(value, list)
            for item in value:
                self.assertIsInstance(item, str)

if __name__ == "__main__":
    unittest.main()
