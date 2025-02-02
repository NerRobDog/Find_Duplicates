# Файл: tests/test_comparer.py
import os
import unittest
import tempfile
import shutil
from find_duplicates.modules.comparer import compare_files, find_potential_duplicates
from find_duplicates.modules.grouper import group_files_by_size


def create_file(dir_path, filename, content):
    """
    Утилита для создания текстового файла.
    Возвращает абсолютный путь к файлу.
    """
    full_path = os.path.join(dir_path, filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full_path)

class TestCompareFiles(unittest.TestCase):
    """
    UnitTest тесты для функции compare_files.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_identical_files(self):
        f1 = create_file(self.temp_dir, "file1.txt", "Hello World")
        f2 = create_file(self.temp_dir, "file2.txt", "Hello World")
        self.assertTrue(compare_files(f1, f2))

    def test_different_files(self):
        a = create_file(self.temp_dir, "a.txt", "abc")
        b = create_file(self.temp_dir, "b.txt", "xyz")
        self.assertFalse(compare_files(a, b))

    def test_empty_files(self):
        e1 = create_file(self.temp_dir, "empty1.txt", "")
        e2 = create_file(self.temp_dir, "empty2.txt", "")
        self.assertTrue(compare_files(e1, e2))

    def test_one_empty_vs_not_empty(self):
        empty = create_file(self.temp_dir, "empty.txt", "")
        not_empty = create_file(self.temp_dir, "not.txt", "some data")
        self.assertFalse(compare_files(empty, not_empty))

    def test_one_byte_diff(self):
        f1 = create_file(self.temp_dir, "f1.txt", "HelloA")
        f2 = create_file(self.temp_dir, "f2.txt", "HelloB")
        self.assertFalse(compare_files(f1, f2))

    def test_large_files(self):
        data = "A" * (2 * 1024 * 1024)
        big1 = create_file(self.temp_dir, "big1.txt", data)
        big2 = create_file(self.temp_dir, "big2.txt", data)
        self.assertTrue(compare_files(big1, big2))

    def test_nonexistent_file(self):
        f1 = create_file(self.temp_dir, "exists.txt", "abc")
        missing = os.path.join(self.temp_dir, "missing.txt")
        # Ожидаем, что функция вернет False при отсутствии файла
        self.assertFalse(compare_files(f1, missing))

    def test_permission_error(self):
        f1 = create_file(self.temp_dir, "p1.txt", "Secret")
        f2 = create_file(self.temp_dir, "p2.txt", "Secret")
        os.chmod(f2, 0o000)
        self.assertFalse(compare_files(f1, f2))
        os.chmod(f2, 0o644)

    def test_unicode_filenames(self):
        uni1 = os.path.join(self.temp_dir, "файл1.txt")
        uni2 = os.path.join(self.temp_dir, "файл2.txt")
        with open(uni1, "w", encoding="utf-8") as f:
            f.write("Unicode content")
        with open(uni2, "w", encoding="utf-8") as f:
            f.write("Unicode content")
        self.assertTrue(compare_files(uni1, uni2))

    def test_repeat_comparison(self):
        f = create_file(self.temp_dir, "repeat.txt", "Repeat data")
        self.assertTrue(compare_files(f, f))
        self.assertTrue(compare_files(f, f))

    @unittest.skipIf(not hasattr(os, "symlink"), "Symlinks not supported")
    def test_compare_symlink(self):
        target = create_file(self.temp_dir, "target.txt", "Symlink content")
        link = os.path.join(self.temp_dir, "link.txt")
        if os.path.exists(link):
            os.remove(link)
        os.symlink(target, link)
        self.assertTrue(compare_files(target, link))

class TestFindPotentialDuplicates(unittest.TestCase):
    """
    UnitTest тесты для функции find_potential_duplicates.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def create_small_file(self, name, content):
        path_ = os.path.join(self.temp_dir, name)
        with open(path_, "w", encoding="utf-8") as f:
            f.write(content)
        return os.path.abspath(path_)

    def test_basic_duplicates(self):
        dup1 = self.create_small_file("dup1.txt", "Duplicate")
        dup2 = self.create_small_file("dup2.txt", "Duplicate")
        unique = self.create_small_file("unique.txt", "Unique")
        grouped = group_files_by_size([dup1, dup2, unique])
        dups = find_potential_duplicates(grouped, "md5")
        self.assertIsInstance(dups, dict)
        found = False
        for hsh, items in dups.items():
            paths = {item["path"] for item in items}
            if {dup1, dup2}.issubset(paths):
                found = True
        self.assertTrue(found)

    def test_no_duplicates_for_diff_files(self):
        a = self.create_small_file("a.txt", "AAA")
        b = self.create_small_file("b.txt", "BBB")
        grouped = group_files_by_size([a, b])
        duplicates = find_potential_duplicates(grouped, "md5")
        self.assertEqual(duplicates, {})

    def test_error_nonexistent_or_no_access(self):
        ok_file = self.create_small_file("ok.txt", "Data")
        missing = os.path.join(self.temp_dir, "missing.txt")
        grouped = group_files_by_size([ok_file, missing])
        dups = find_potential_duplicates(grouped, "md5")
        self.assertIsInstance(dups, dict)

    def test_same_size_diff_content(self):
        f1 = self.create_small_file("coll1.txt", "abc")
        f2 = self.create_small_file("coll2.txt", "abd")
        grouped = group_files_by_size([f1, f2])
        duplicates = find_potential_duplicates(grouped, "md5")
        self.assertEqual(duplicates, {})

    def test_big_files_duplicates(self):
        data = "Z" * (2 * 1024 * 1024)
        file1 = self.create_small_file("bigA.txt", data)
        file2 = self.create_small_file("bigB.txt", data)
        grouped = group_files_by_size([file1, file2])
        dups = find_potential_duplicates(grouped, "sha256")
        self.assertEqual(len(dups), 1)
        items = list(dups.values())[0]
        paths = {item["path"] for item in items}
        self.assertEqual(paths, {file1, file2})

    def test_permission_error_in_duplicates(self):
        ok_file = self.create_small_file("ok.txt", "some data")
        blocked = self.create_small_file("blocked.txt", "some data")
        os.chmod(blocked, 0o000)
        grouped = group_files_by_size([ok_file, blocked])
        dups = find_potential_duplicates(grouped, "md5")
        self.assertEqual(dups, {})
        os.chmod(blocked, 0o644)

    def test_unicode_filename_duplicates(self):
        f1 = self.create_small_file("файл1.txt", "Unicode data")
        f2 = self.create_small_file("файл2.txt", "Unicode data")
        grouped = group_files_by_size([f1, f2])
        dups = find_potential_duplicates(grouped, "md5")
        self.assertEqual(len(dups), 1)
        items = list(dups.values())[0]
        paths = {item["path"] for item in items}
        self.assertEqual(paths, {f1, f2})

    def test_duplicates_stability(self):
        f1 = self.create_small_file("a.txt", "DupData")
        f2 = self.create_small_file("b.txt", "DupData")
        grouped = group_files_by_size([f1, f2])
        d1 = find_potential_duplicates(grouped, "md5")
        d2 = find_potential_duplicates(grouped, "md5")
        self.assertEqual(d1, d2)

if __name__ == "__main__":
    unittest.main()