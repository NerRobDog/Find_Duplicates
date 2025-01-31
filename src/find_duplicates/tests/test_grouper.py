import unittest
import coverage
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
        self.special_file = "файл_üñîçødé.txt"
        self.binary_file = "test_binary.bin"
        self.protected_file = "protected.txt"
        self.directory = "test_directory"

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

        # Создание бинарного файла
        with open(self.binary_file, "wb") as f:
            f.write(b"\x00" * 10)

        # Файл с особыми символами в названии
        with open(self.special_file, "wb") as f:
            f.write(b"Special Content")

        # Файл с защитой
        with open(self.protected_file, "wb") as f:
            f.write(b"Protected")
        os.chmod(self.protected_file, 0o000)

        # Создание директории
        os.mkdir(self.directory)

    def tearDown(self):
        """Удаляет тестовые файлы после выполнения тестов"""
        for file in [
            self.file1, self.file2, self.file3, self.file4, self.file5,
            self.file6, self.file7, self.symlink, self.special_file,
            self.binary_file, self.protected_file
        ]:
            if os.path.exists(file) or os.path.islink(file):
                os.remove(file)

        if os.path.exists(self.directory):
            os.rmdir(self.directory)

    def test_group_files_by_size_protected_file(self):
        """Тестирует обработку защищенного файла (PermissionError)"""
        result = group_files_by_size([self.protected_file])
        self.assertEqual({}, result)
        os.chmod(self.protected_file, 0o644)  # Возвращаем доступ

    def test_group_files_by_size_binary_file(self):
        """Тестирует обработку бинарного файла"""
        result = group_files_by_size([self.binary_file])
        expected_size = os.path.getsize(self.binary_file)
        self.assertIn(expected_size, result)

    def test_group_files_by_size_special_filename(self):
        """Тестирует обработку файла с особыми символами в названии"""
        result = group_files_by_size([self.special_file])
        expected_size = os.path.getsize(self.special_file)
        self.assertIn(expected_size, result)

    def test_group_files_by_size_directory(self):
        """Тестирует обработку попытки группировки директории как файла"""
        result = group_files_by_size([self.directory])
        self.assertEqual({}, result)


if __name__ == "__main__":
    cov = coverage.Coverage(source=["find_duplicates/modules"], branch=True)
    cov.start()

    try:
        unittest.main()
    finally:
        cov.stop()
        cov.save()
        cov.report()
        cov.html_report(directory="htmlcov")
