import os
import tempfile
import shutil
import unittest
from parameterized import parameterized
import hashlib

from find_duplicates.modules.comparer import compare_files, find_potential_duplicates
from find_duplicates.modules.grouper import group_files_by_size


class TestCompareFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # Параметризованные тесты для простых случаев (текстовые файлы)
    @parameterized.expand([
        ("identical_text", "Hello World", "Hello World", True),
        ("different_text", "Hello", "World", False),
        ("empty_files", "", "", True),
        ("one_empty_one_nonempty", "", "Data", False),
    ])
    def test_compare_files_text(self, name, content1, content2, expected):
        file1 = os.path.join(self.test_dir, f"file1_{name}.txt")
        file2 = os.path.join(self.test_dir, f"file2_{name}.txt")
        with open(file1, "w", encoding="utf-8") as f:
            f.write(content1)
        with open(file2, "w", encoding="utf-8") as f:
            f.write(content2)
        result = compare_files(file1, file2)
        self.assertEqual(result, expected)

    def test_compare_files_binary(self):
        # Два бинарных файла с одинаковым содержимым
        file1 = os.path.join(self.test_dir, "binary1.bin")
        file2 = os.path.join(self.test_dir, "binary2.bin")
        data = os.urandom(1024)
        with open(file1, "wb") as f:
            f.write(data)
        with open(file2, "wb") as f:
            f.write(data)
        result = compare_files(file1, file2)
        self.assertTrue(result)

    def test_compare_files_small_difference(self):
        # Файлы, отличающиеся одной байтовой разницей
        file1 = os.path.join(self.test_dir, "diff1.txt")
        file2 = os.path.join(self.test_dir, "diff2.txt")
        data1 = b"1234567890"
        data2 = b"1234567891"  # отличается последним байтом
        with open(file1, "wb") as f:
            f.write(data1)
        with open(file2, "wb") as f:
            f.write(data2)
        result = compare_files(file1, file2)
        self.assertFalse(result)

    def test_compare_files_nonexistent(self):
        # Один из файлов не существует – ожидается исключение (или обработка ошибки)
        file1 = os.path.join(self.test_dir, "exists.txt")
        file2 = os.path.join(self.test_dir, "nonexistent.txt")
        with open(file1, "w") as f:
            f.write("Data")
        with self.assertRaises(Exception):
            compare_files(file1, file2)

    def test_compare_files_permission_error(self):
        # Файлы с ошибкой доступа
        file1 = os.path.join(self.test_dir, "perm1.txt")
        file2 = os.path.join(self.test_dir, "perm2.txt")
        with open(file1, "w") as f:
            f.write("Secret")
        with open(file2, "w") as f:
            f.write("Secret")
        os.chmod(file2, 0o000)  # Убираем права на чтение
        try:
            with self.assertRaises(Exception):
                compare_files(file1, file2)
        finally:
            os.chmod(file2, 0o644)

    def test_compare_files_large(self):
        # Сравнение больших файлов (например, 1МБ одинакового контента)
        file1 = os.path.join(self.test_dir, "large1.txt")
        file2 = os.path.join(self.test_dir, "large2.txt")
        data = "A" * (1024 * 1024)  # 1 МБ символов "A"
        with open(file1, "w") as f:
            f.write(data)
        with open(file2, "w") as f:
            f.write(data)
        result = compare_files(file1, file2)
        self.assertTrue(result)

    def test_compare_files_unicode_filenames(self):
        # Файлы с non‑ASCII именами
        file1 = os.path.join(self.test_dir, "файл1.txt")
        file2 = os.path.join(self.test_dir, "файл2.txt")
        with open(file1, "w", encoding="utf-8") as f:
            f.write("Unicode content")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("Unicode content")
        result = compare_files(file1, file2)
        self.assertTrue(result)

    def test_repeat_comparison(self):
        # Повторное сравнение одного и того же файла
        file1 = os.path.join(self.test_dir, "repeat.txt")
        with open(file1, "w") as f:
            f.write("Repeat")
        result1 = compare_files(file1, file1)
        result2 = compare_files(file1, file1)
        self.assertTrue(result1)
        self.assertTrue(result2)

    def test_compare_files_symlink(self):
        # Сравнение файла и его симлинка
        if not hasattr(os, "symlink"):
            self.skipTest("Симлинки не поддерживаются в этой ОС")
        target = os.path.join(self.test_dir, "target.txt")
        symlink = os.path.join(self.test_dir, "link.txt")
        with open(target, "w") as f:
            f.write("Symlink test")
        os.symlink(target, symlink)
        result = compare_files(target, symlink)
        self.assertTrue(result)

    def test_stability_multiple_calls(self):
        # Повторное последовательное сравнение для проверки стабильности
        file1 = os.path.join(self.test_dir, "stable.txt")
        file2 = os.path.join(self.test_dir, "stable2.txt")
        with open(file1, "w") as f:
            f.write("Stable content")
        with open(file2, "w") as f:
            f.write("Stable content")
        for _ in range(5):
            result = compare_files(file1, file2)
            self.assertTrue(result)


class TestFindPotentialDuplicates(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_find_duplicates_grouping(self):
        # Создаём три файла: два с одинаковым содержимым и один с другим содержимым
        file1 = os.path.join(self.test_dir, "dup1.txt")
        file2 = os.path.join(self.test_dir, "dup2.txt")
        file3 = os.path.join(self.test_dir, "unique.txt")
        content_dup = "Duplicate content"
        content_unique = "Unique content"
        with open(file1, "w") as f:
            f.write(content_dup)
        with open(file2, "w") as f:
            f.write(content_dup)
        with open(file3, "w") as f:
            f.write(content_unique)

        # Сначала группируем файлы по размеру
        grouped = group_files_by_size([file1, file2, file3])
        # Вызываем find_potential_duplicates (ожидается группировка по хэшу)
        duplicates = find_potential_duplicates(grouped, "md5")
        # Проверяем, что в одной из групп находятся file1 и file2
        found = any(set(group) == {file1, file2} for group in duplicates.values())
        self.assertTrue(found, "Дубликаты не сгруппированы корректно")

    def test_find_duplicates_no_false_positives(self):
        # Файлы с различным содержимым не должны сгруппироваться вместе
        file1 = os.path.join(self.test_dir, "a.txt")
        file2 = os.path.join(self.test_dir, "b.txt")
        with open(file1, "w") as f:
            f.write("Content A")
        with open(file2, "w") as f:
            f.write("Content B")
        grouped = group_files_by_size([file1, file2])
        duplicates = find_potential_duplicates(grouped, "md5")
        # Ожидаем, что ни одна группа не содержит более одного файла
        for group in duplicates.values():
            self.assertLess(len(group), 2, "Несовпадающие файлы сгруппированы как дубликаты")

    def test_find_duplicates_error_handling(self):
        # Проверка обработки ошибочных данных – если grouped не соответствует ожидаемой структуре
        grouped = {"invalid_key": ["nonexistent_file.txt"]}
        try:
            duplicates = find_potential_duplicates(grouped, "md5")
            self.assertIsInstance(duplicates, dict)
        except Exception as e:
            self.fail(f"find_potential_duplicates вызвала исключение: {e}")


if __name__ == "__main__":
    unittest.main()
