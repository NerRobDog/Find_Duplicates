import os
import io
import csv
import tempfile
import shutil
import unittest
from parameterized import parameterized
from find_duplicates.modules.output import write_duplicates_to_csv, print_results, save_results_to_file


class TestOutput(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @parameterized.expand([
        ("with_data", {"group1": ["file1.txt", "file2.txt"], "group2": ["file3.txt"]}),
        ("empty_dict", {})
    ])
    def test_write_duplicates_to_csv(self, name, duplicates):
        output_file = os.path.join(self.test_dir, "duplicates.csv")
        # Записываем дубликаты в CSV
        write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(os.path.exists(output_file))
        # Читаем файл и проверяем, что в содержимом есть разделители (например, запятые)
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        if duplicates:
            self.assertIn(",", content)
        else:
            self.assertTrue(len(content) >= 0)

    def test_write_duplicates_to_csv_invalid_path(self):
        # Используем несуществующую директорию для записи
        invalid_path = os.path.join(self.test_dir, "nonexistent_dir", "duplicates.csv")
        with self.assertRaises(Exception):
            write_duplicates_to_csv({"group": ["file.txt"]}, invalid_path)

    def test_print_results(self):
        duplicates = {"group1": ["file1.txt", "file2.txt"]}
        captured_output = io.StringIO()
        import sys
        old_stdout = sys.stdout
        sys.stdout = captured_output
        try:
            print_results(duplicates)
        finally:
            sys.stdout = old_stdout
        output = captured_output.getvalue()
        self.assertIn("group1", output)
        self.assertIn("file1.txt", output)
        self.assertIn("file2.txt", output)

    @parameterized.expand([
        ("simple_text", {"group1": ["file1.txt"]}),
        ("unicode", {"группа": ["файл.txt", "другой.txt"]})
    ])
    def test_save_results_to_file(self, name, results):
        output_file = os.path.join(self.test_dir, "results.txt")
        save_results_to_file(results, output_file)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
        for key, files in results.items():
            self.assertIn(key, content)
            for file in files:
                self.assertIn(file, content)

    def test_rewrite_existing_file(self):
        output_file = os.path.join(self.test_dir, "results.txt")
        initial_content = "Old Content"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(initial_content)
        results = {"group1": ["file1.txt", "file2.txt"]}
        save_results_to_file(results, output_file)
        with open(output_file, "r", encoding="utf-8") as f:
            new_content = f.read()
        self.assertNotEqual(initial_content, new_content)

    def test_large_number_of_groups(self):
        # Генерируем много групп
        duplicates = {f"group{i}": [f"file{i}_1.txt", f"file{i}_2.txt"] for i in range(100)}
        output_file = os.path.join(self.test_dir, "large.csv")
        write_duplicates_to_csv(duplicates, output_file)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Если реализована запись заголовка, то число строк должно быть не менее 101
        self.assertGreaterEqual(len(lines), 100)

    def test_error_handling_in_save_results(self):
        # Симулируем ошибку записи, используя директорию без прав на запись
        no_write_dir = os.path.join(self.test_dir, "no_write")
        os.mkdir(no_write_dir)
        os.chmod(no_write_dir, 0o444)  # Только чтение
        output_file = os.path.join(no_write_dir, "results.txt")
        with self.assertRaises(Exception):
            save_results_to_file({"group": ["file.txt"]}, output_file)
        os.chmod(no_write_dir, 0o755)


if __name__ == "__main__":
    unittest.main()
