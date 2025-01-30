import unittest
import os
from ..modules.grouper import group_files_by_size


class TestGrouper(unittest.TestCase):
    def setUp(self):
        """Создаёт тестовые файлы перед запуском тестов"""
        self.file1 = "test_file_1.txt"
        self.file2 = "test_file_2.txt"
        self.file3 = "test_file_3.txt"
        self.file4 = "test_empty_1.txt"
        self.file5 = "test_empty_2.txt"
        self.file6 = "test_large_1.txt"
        self.file7 = "test_large_2.txt"
        self.symlink = "test_symlink.txt"

        # Создание файлов с содержимым
        with open(self.file1, "wb") as f:
            f.write(b"Hello")

        with open(self.file2, "wb") as f:
            f.write(b"Hello")

        with open(self.file3, "wb") as f:
            f.write(b"Python")

        # Создание пустых файлов
        open(self.file4, "wb").close()
        open(self.file5, "wb").close()

        # Создание больших файлов (~1MB)
        with open(self.file6, "wb") as f:
            f.write(b"A" * 1024 * 1024)  # 1MB

        with open(self.file7, "wb") as f:
            f.write(b"A" * 1024 * 1024)  # 1MB

        # Создание символической ссылки (если ОС поддерживает)
        if hasattr(os, "symlink"):
            os.symlink(self.file1, self.symlink)

    def tearDown(self):
        """Удаляет тестовые файлы после выполнения тестов"""
        for file in [
            self.file1, self.file2, self.file3, self.file4, self.file5, self.file6, self.file7, self.symlink
        ]:
            if os.path.exists(file) or os.path.islink(file):
                os.remove(file)

    def test_group_files_by_size_empty_list(self):
        """Проверка на пустой список файлов"""
        result = group_files_by_size([])
        self.assertEqual(result, {})

    def test_group_files_by_size_single_file(self):
        """Проверка с одним файлом"""
        result = group_files_by_size([self.file1])
        expected_size = os.path.getsize(self.file1)

        self.assertIn(expected_size, result)
        self.assertEqual(result[expected_size], [self.file1])

    def test_group_files_by_size_multiple_files_same_size(self):
        """Проверка с несколькими файлами одинакового размера"""
        result = group_files_by_size([self.file1, self.file2])
        expected_size = os.path.getsize(self.file1)

        self.assertIn(expected_size, result)
        self.assertEqual(sorted(result[expected_size]), sorted([self.file1, self.file2]))

    def test_group_files_by_size_multiple_files_different_sizes(self):
        """Проверка с несколькими файлами разного размера"""
        result = group_files_by_size([self.file1, self.file3])

        size1 = os.path.getsize(self.file1)
        size2 = os.path.getsize(self.file3)

        self.assertIn(size1, result)
        self.assertIn(size2, result)
        self.assertEqual(result[size1], [self.file1])
        self.assertEqual(result[size2], [self.file3])

    def test_group_files_by_size_file_not_found(self):
        """Проверка с несуществующим файлом"""
        non_existent_file = "non_existent_file.txt"
        result = group_files_by_size([non_existent_file])

        self.assertEqual(result, {})

    def test_group_files_by_size_empty_files(self):
        """Проверка с пустыми файлами"""
        result = group_files_by_size([self.file4, self.file5])
        expected_size = os.path.getsize(self.file4)  # Оба файла должны иметь размер 0

        self.assertIn(expected_size, result)
        self.assertEqual(sorted(result[expected_size]), sorted([self.file4, self.file5]))

    def test_group_files_by_size_large_files(self):
        """Проверка с большими файлами (1MB)"""
        result = group_files_by_size([self.file6, self.file7])
        expected_size = os.path.getsize(self.file6)

        self.assertIn(expected_size, result)
        self.assertEqual(sorted(result[expected_size]), sorted([self.file6, self.file7]))

    def test_group_files_by_size_mixed_sizes(self):
        """Проверка с файлами разного размера, но некоторыми одинаковыми"""
        result = group_files_by_size([self.file1, self.file2, self.file3])

        size1 = os.path.getsize(self.file1)
        size2 = os.path.getsize(self.file3)

        self.assertIn(size1, result)
        self.assertIn(size2, result)
        self.assertEqual(sorted(result[size1]), sorted([self.file1, self.file2]))
        self.assertEqual(result[size2], [self.file3])

    def test_group_files_by_size_symlinks(self):
        """Проверка с символическими ссылками"""
        if not hasattr(os, "symlink"):
            self.skipTest("ОС не поддерживает символические ссылки")

        result = group_files_by_size([self.file1, self.symlink])
        expected_size = os.path.getsize(self.file1)

        self.assertIn(expected_size, result)
        self.assertEqual(sorted(result[expected_size]), sorted([self.file1, self.symlink]))

    def test_group_files_by_size_large_dataset(self):
        """Проверка с большим набором файлов"""
        large_files = []
        for i in range(10):
            filename = f"test_large_{i}.txt"
            with open(filename, "wb") as f:
                f.write(b"X" * 5000)  # 5 KB файлы
            large_files.append(filename)

        result = group_files_by_size(large_files)

        expected_size = os.path.getsize(large_files[0])
        self.assertIn(expected_size, result)
        self.assertEqual(sorted(result[expected_size]), sorted(large_files))

        for file in large_files:
            os.remove(file)


if __name__ == '__main__':
    unittest.main()
