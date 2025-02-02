# Файл: tests/test_output.py
import os
import unittest
import tempfile
import shutil
from find_duplicates.modules.output import write_duplicates_to_csv, print_tree_view, save_tree_to_txt
from io import StringIO
from unittest.mock import patch


class TestOutputCSV(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_write_duplicates_to_csv_valid(self):
        """
        Запись корректного словаря в CSV.
        """
        output_file = os.path.join(self.temp_dir, "duplicates.csv")
        duplicates = {
            "hash123": [
                {"path": "/some/path/file1.txt", "size": 123},
                {"path": "/some/path/file2.txt", "size": 123}
            ],
            "hash456": [
                {"path": "/some/path/file3.txt", "size": 456}
            ]
        }
        result = write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(",", content)
            self.assertIn("Группа,Путь,Размер", content)

    def test_write_duplicates_to_csv_empty(self):
        """
        Запись пустого словаря => только заголовок
        """
        output_file = os.path.join(self.temp_dir, "duplicates_empty.csv")
        duplicates = {}
        result = write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(result)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Группа,Путь,Размер", content)

    def test_write_duplicates_to_csv_invalid_path(self):
        """
        Указываем путь в несуществующую директорию => ожидаем False
        """
        invalid_dir = os.path.join(self.temp_dir, "nonexistent_dir")
        output_file = os.path.join(invalid_dir, "output.csv")
        duplicates = {"hash000": [{"path": "dummy.txt", "size": 100}]}
        result = write_duplicates_to_csv(duplicates, output_file)
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_file))

    def test_write_duplicates_to_csv_unicode(self):
        """
        Корректная запись unicode-символов.
        """
        output_file = os.path.join(self.temp_dir, "uni.csv")
        duplicates = {
            "hashUni": [
                {"path": "/tmp/файл.txt", "size": 50},
                {"path": "/tmp/другой_файл.txt", "size": 50},
            ]
        }
        result = write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(result)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("файл.txt", content)

    def test_write_duplicates_to_csv_many_groups(self):
        """
        Большое количество групп => проверяем, что всё записывается без ошибок.
        """
        output_file = os.path.join(self.temp_dir, "many.csv")
        duplicates = {}
        for i in range(100):
            hsh = f"hash{i}"
            duplicates[hsh] = [
                {"path": f"/path/to/file{i}_1.txt", "size": 1234},
                {"path": f"/path/to/file{i}_2.txt", "size": 1234}
            ]
        result = write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(result)
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertGreaterEqual(len(lines), 201)

    def test_rewrite_csv(self):
        """
        Проверяем перезапись файла.
        """
        output_file = os.path.join(self.temp_dir, "rewrite.csv")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("OLD CONTENT")

        duplicates = {
            "hashXYZ": [
                {"path": "/path/fileA.txt", "size": 500},
                {"path": "/path/fileB.txt", "size": 500}
            ]
        }
        result = write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(result)
        with open(output_file, "r", encoding="utf-8") as f:
            new_content = f.read()
            self.assertNotIn("OLD CONTENT", new_content)


class TestOutputTree(unittest.TestCase):
    def test_print_tree_view(self):
        duplicates = {
            "hash123": [
                {"path": "/some/path1.txt", "size": 100},
                {"path": "/some/path2.txt", "size": 100},
            ]
        }
        # Перенаправим stdout в StringIO
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print_tree_view(duplicates)
            output = fake_out.getvalue()
            self.assertIn("Группа 1:", output)
            self.assertIn("/some/path1.txt", output)

    def test_save_tree_to_txt(self):
        duplicates = {
            "hashUni": [
                {"path": "/tmp/файл.txt", "size": 50},
                {"path": "/tmp/другой.txt", "size": 50}
            ]
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, "tree.txt")
            save_tree_to_txt(duplicates, out_file)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("Группа 1:", content)
                self.assertIn("файл.txt", content)

    def test_save_tree_no_permission(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            locked_dir = os.path.join(tmp_dir, "locked")
            os.mkdir(locked_dir)
            os.chmod(locked_dir, 0o444)
            out_file = os.path.join(locked_dir, "results.txt")

            duplicates = {"hashX": [{"path": "/path/f.txt", "size": 100}]}
            with self.assertRaises(Exception):
                save_tree_to_txt(duplicates, out_file)

            os.chmod(locked_dir, 0o755)


if __name__ == "__main__":
    unittest.main()
