import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch

from find_duplicates.find_duplicates import main
from find_duplicates.modules.utils import parse_arguments


class TestFindDuplicatesIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_csv = os.path.join(self.test_dir, "output.csv")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # --------------------- A. Парсинг аргументов ---------------------
    def test_A1_missing_directory_argument(self):
        test_args = ["prog", "--exclude", "*.tmp"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()

    def test_A2_unknown_flag(self):
        test_args = ["prog", "--directory", self.test_dir, "--unknown", "value"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()

    def test_A3_invalid_hash_type(self):
        test_args = ["prog", "--directory", self.test_dir, "--hash-type", "invalid"]
        with patch.object(sys, "argv", test_args):
            with self.assertRaises(SystemExit):
                parse_arguments()

    def test_A4_log_level_changes(self):
        # Создаем dummy-файл, чтобы сканирование прошло успешно
        dummy = os.path.join(self.test_dir, "dummy.txt")
        with open(dummy, "w", encoding="utf-8") as f:
            f.write("dummy")
        test_args = ["prog", "--directory", self.test_dir, "--log-level", "DEBUG", "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except Exception:
                self.fail("main() вызвал исключение с корректными аргументами.")

    def test_A5_skip_inaccessible(self):
        # Без флага --skip-inaccessible => CSV не создаётся, т.к. будет ошибка доступа
        inac = os.path.join(self.test_dir, "inac.txt")
        with open(inac, "w", encoding="utf-8") as f:
            f.write("secret")
        os.chmod(inac, 0o000)

        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        # При ошибке доступа CSV не должно создаться
        self.assertFalse(os.path.exists(self.output_csv))

        # Теперь добавляем --skip-inaccessible => создаётся CSV (скорее всего с заголовком)
        os.chmod(inac, 0o000)
        test_args.append("--skip-inaccessible")
        with patch.object(sys, "argv", test_args):
            main()
        self.assertTrue(os.path.exists(self.output_csv))
        os.chmod(inac, 0o644)

    # --------------------- B. Валидация директории ---------------------
    def test_B1_nonexistent_directory(self):
        non_exist = os.path.join(self.test_dir, "no_dir")
        output_file = os.path.join(self.test_dir, "out.csv")
        test_args = ["prog", "--directory", non_exist, "--output", output_file]
        with patch.object(sys, "argv", test_args):
            main()
        # При ошибке проверки директории CSV не создаётся
        self.assertFalse(os.path.exists(output_file))

    def test_B2_directory_no_permission(self):
        locked = os.path.join(self.test_dir, "locked")
        os.mkdir(locked)
        os.chmod(locked, 0o000)
        test_args = ["prog", "--directory", locked, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        # При отсутствии прав CSV не создаётся
        self.assertFalse(os.path.exists(self.output_csv))
        os.chmod(locked, 0o755)

    def test_B3_valid_directory(self):
        dummy = os.path.join(self.test_dir, "dummy.txt")
        with open(dummy, "w", encoding="utf-8") as f:
            f.write("dummy")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            try:
                main()
            except Exception:
                self.fail("main() вызвал исключение для корректной директории.")
            self.assertTrue(os.path.exists(self.output_csv))

    # --------------------- C. Сканирование ---------------------
    def test_C1_empty_folder(self):
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("Файлы не найдены" in content or content.strip() == "Группа,Путь,Размер")

    def test_C2_include_hidden_false(self):
        # Один файл visible.txt => нет дубликатов => CSV = только заголовок
        visible = os.path.join(self.test_dir, "visible.txt")
        with open(visible, "w", encoding="utf-8") as f:
            f.write("data")
        hidden = os.path.join(self.test_dir, ".hidden.txt")
        with open(hidden, "w", encoding="utf-8") as f:
            f.write("hidden")

        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, "Группа,Путь,Размер")

    def test_C3_include_hidden_true(self):
        # Аналогично => нет дубликатов => только заголовок
        hidden = os.path.join(self.test_dir, ".hidden.txt")
        with open(hidden, "w", encoding="utf-8") as f:
            f.write("hidden")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv, "--include-hidden"]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, "Группа,Путь,Размер")

    def test_C4_exclude_extension(self):
        # Исключили *.tmp => остался один файл => нет дубликатов => только заголовок
        tmp_file = os.path.join(self.test_dir, "file.tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write("temp")
        normal = os.path.join(self.test_dir, "file.txt")
        with open(normal, "w", encoding="utf-8") as f:
            f.write("text")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv, "--exclude", "*.tmp"]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, "Группа,Путь,Размер")

    def test_C5_skip_inaccessible_scan(self):
        # При skip_inaccessible недоступный файл просто не сканируется => если остался 0 или 1 файл => только заголовок
        inac = os.path.join(self.test_dir, "inac.txt")
        with open(inac, "w", encoding="utf-8") as f:
            f.write("secret")
        os.chmod(inac, 0o000)

        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv, "--skip-inaccessible"]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("inac.txt", content)
        os.chmod(inac, 0o644)

    # --------------------- D. Группировка ---------------------
    def test_D1_no_grouping(self):
        # Файлы с разным размером => нет групп => "Нет групп..." или только заголовок
        unique1 = os.path.join(self.test_dir, "unique1.txt")
        unique2 = os.path.join(self.test_dir, "unique2.txt")
        with open(unique1, "w", encoding="utf-8") as f:
            f.write("data1")
        with open(unique2, "w", encoding="utf-8") as f:
            f.write("data2")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("Нет групп" in content or content.strip() == "Группа,Путь,Размер")

    def test_D2_grouping_proceeds(self):
        # Два файла одинакового размера => уже появляется "Группа"
        dup1 = os.path.join(self.test_dir, "dup1.txt")
        dup2 = os.path.join(self.test_dir, "dup2.txt")
        with open(dup1, "w", encoding="utf-8") as f:
            f.write("duplicate")
        with open(dup2, "w", encoding="utf-8") as f:
            f.write("duplicate")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Группа", content)
        self.assertIn("dup1.txt", content)
        self.assertIn("dup2.txt", content)

    # --------------------- E. Поиск потенциальных дубликатов ---------------------
    def test_E1_different_content(self):
        # Один размер, но разное содержание => "Дубликаты не обнаружены" или только заголовок
        f1 = os.path.join(self.test_dir, "f1.txt")
        f2 = os.path.join(self.test_dir, "f2.txt")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("Content A")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("Content B")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("Дубликаты не обнаружены" in content or content.strip() == "Группа,Путь,Размер")

    def test_E2_real_duplicates(self):
        # Контент совпадает => ожидаем реальную группу
        dup1 = os.path.join(self.test_dir, "dup1.txt")
        dup2 = os.path.join(self.test_dir, "dup2.txt")
        with open(dup1, "w", encoding="utf-8") as f:
            f.write("SameContent")
        with open(dup2, "w", encoding="utf-8") as f:
            f.write("SameContent")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Группа", content)
        self.assertIn("dup1.txt", content)
        self.assertIn("dup2.txt", content)

    def test_E3_hash_type_variants(self):
        # Проверяем разные типы хэшей (md5, sha256, blake3 при наличии)
        for ht in ["md5", "sha256"]:
            dup1 = os.path.join(self.test_dir, f"dup1_{ht}.txt")
            dup2 = os.path.join(self.test_dir, f"dup2_{ht}.txt")
            with open(dup1, "w", encoding="utf-8") as f:
                f.write("ContentX")
            with open(dup2, "w", encoding="utf-8") as f:
                f.write("ContentX")
            test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv, "--hash-type", ht]
            with patch.object(sys, "argv", test_args):
                main()
            with open(self.output_csv, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Группа", content)

        # Проверяем blake3, если установлено
        try:
            import blake3
            available = True
        except ImportError:
            available = False
        if available:
            dup1 = os.path.join(self.test_dir, "dup1_blake3.txt")
            dup2 = os.path.join(self.test_dir, "dup2_blake3.txt")
            with open(dup1, "w", encoding="utf-8") as f:
                f.write("ContentY")
            with open(dup2, "w", encoding="utf-8") as f:
                f.write("ContentY")
            test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv, "--hash-type", "blake3"]
            with patch.object(sys, "argv", test_args):
                main()
            with open(self.output_csv, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Группа", content)

    def test_E4_special_names(self):
        # Проверяем корректность экранирования кавычек
        special_files = [
            'John\'s file.txt',
            'some "quote".txt',
            'Пример_файл🙂.txt'
        ]
        for fname in special_files:
            path = os.path.join(self.test_dir, fname)
            with open(path, "w", encoding="utf-8") as f:
                f.write("SpecialContent")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        # Если нет дубликатов, "Группа" может не появиться, но убедимся, что
        # экранирование для двойных кавычек есть (some ""quote"".txt)
        for fname in special_files:
            if '"' in fname:
                escaped = fname.replace('"', '""')
                self.assertIn(escaped, content)
            else:
                self.assertIn(fname, content)

    # --------------------- F. Вывод CSV ---------------------
    def test_F1_csv_success(self):
        dup1 = os.path.join(self.test_dir, "dup1.txt")
        dup2 = os.path.join(self.test_dir, "dup2.txt")
        with open(dup1, "w", encoding="utf-8") as f:
            f.write("Dup")
        with open(dup2, "w", encoding="utf-8") as f:
            f.write("Dup")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        self.assertTrue(os.path.exists(self.output_csv))
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Группа", content)
        self.assertIn("dup1.txt", content)

    def test_F2_csv_write_error(self):
        # Если нет прав на запись => main() логирует ошибку => программа завершается
        dup1 = os.path.join(self.test_dir, "dup1.txt")
        dup2 = os.path.join(self.test_dir, "dup2.txt")
        with open(dup1, "w", encoding="utf-8") as f:
            f.write("Dup")
        with open(dup2, "w", encoding="utf-8") as f:
            f.write("Dup")
        locked_dir = os.path.join(self.test_dir, "locked")
        os.mkdir(locked_dir)
        os.chmod(locked_dir, 0o400)
        error_csv = os.path.join(locked_dir, "out.csv")
        test_args = ["prog", "--directory", self.test_dir, "--output", error_csv]
        with patch.object(sys, "argv", test_args):
            # Раньше ожидался raise Exception,
            # но теперь main() просто логирует и выходит (можно проверить, что CSV не создан)
            main()
        os.chmod(locked_dir, 0o700)
        self.assertFalse(os.path.exists(error_csv))

    # --------------------- G. Интеграционные сценарии ---------------------
    def test_G1_empty_folder(self):
        # Пустая папка => "Файлы не найдены..." + CSV с заголовком
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("Файлы не найдены" in content or content.strip() == "Группа,Путь,Размер")

    def test_G2_multiple_duplicates(self):
        # Две пары дубликатов => CSV содержит их
        dupA1 = os.path.join(self.test_dir, "dupA1.txt")
        dupA2 = os.path.join(self.test_dir, "dupA2.txt")
        dupB1 = os.path.join(self.test_dir, "dupB1.txt")
        dupB2 = os.path.join(self.test_dir, "dupB2.txt")
        with open(dupA1, "w", encoding="utf-8") as f:
            f.write("SetA")
        with open(dupA2, "w", encoding="utf-8") as f:
            f.write("SetA")
        with open(dupB1, "w", encoding="utf-8") as f:
            f.write("SetB")
        with open(dupB2, "w", encoding="utf-8") as f:
            f.write("SetB")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("dupA1.txt", content)
        self.assertIn("dupA2.txt", content)
        self.assertIn("dupB1.txt", content)
        self.assertIn("dupB2.txt", content)

    def test_G3_mixed_scenario(self):
        # include-hidden => ".hidden.txt" учитывается
        # skip-inaccessible => "inac.txt" пропускается
        # exclude="*.tmp" => "temp.tmp" пропускается
        normal = os.path.join(self.test_dir, "normal.txt")
        with open(normal, "w", encoding="utf-8") as f:
            f.write("Data")
        hidden = os.path.join(self.test_dir, ".hidden.txt")
        with open(hidden, "w", encoding="utf-8") as f:
            f.write("Hidden")
        excl = os.path.join(self.test_dir, "temp.tmp")
        with open(excl, "w", encoding="utf-8") as f:
            f.write("Temp")
        inac = os.path.join(self.test_dir, "inac.txt")
        with open(inac, "w", encoding="utf-8") as f:
            f.write("Secret")
        os.chmod(inac, 0o000)

        test_args = [
            "prog", "--directory", self.test_dir, "--output", self.output_csv,
            "--include-hidden", "--exclude", "*.tmp", "--skip-inaccessible"
        ]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        # normal.txt и .hidden.txt должны быть в CSV
        # inac.txt и temp.tmp – нет
        self.assertIn("normal.txt", content)
        self.assertIn(".hidden.txt", content)
        self.assertNotIn("temp.tmp", content)
        self.assertNotIn("inac.txt", content)
        os.chmod(inac, 0o644)

    def test_G4_large_files(self):
        large1 = os.path.join(self.test_dir, "large1.txt")
        large2 = os.path.join(self.test_dir, "large2.txt")
        data = "X" * (4 * 1024 * 1024)
        with open(large1, "w", encoding="utf-8") as f:
            f.write(data)
        with open(large2, "w", encoding="utf-8") as f:
            f.write(data)
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("large1.txt", content)
        self.assertIn("large2.txt", content)

    def test_G5_no_duplicates(self):
        unique1 = os.path.join(self.test_dir, "unique1.txt")
        unique2 = os.path.join(self.test_dir, "unique2.txt")
        with open(unique1, "w", encoding="utf-8") as f:
            f.write("Unique1")
        with open(unique2, "w", encoding="utf-8") as f:
            f.write("Unique2")
        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue("Дубликаты не обнаружены" in content or content.strip() == "Группа,Путь,Размер")

    # --------------------- H. Спецсимволы ---------------------
    def test_H_special_characters(self):
        # Четыре файла (двойные кавычки, одинарная, пробелы, юникод) => если нет дубликатов,
        # всё равно должны попасть в CSV (каждое по своей строке).
        file1 = os.path.join(self.test_dir, 'some "quote".txt')
        with open(file1, "w", encoding="utf-8") as f:
            f.write("Special")
        file2 = os.path.join(self.test_dir, "John's file.txt")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("Special")
        sub_dir = os.path.join(self.test_dir, "My Documents")
        os.mkdir(sub_dir)
        file3 = os.path.join(sub_dir, "Annual report.pdf")
        with open(file3, "w", encoding="utf-8") as f:
            f.write("Special")
        file4 = os.path.join(self.test_dir, "Пример_файл🙂.txt")
        with open(file4, "w", encoding="utf-8") as f:
            f.write("Special")

        test_args = ["prog", "--directory", self.test_dir, "--output", self.output_csv]
        with patch.object(sys, "argv", test_args):
            main()
        with open(self.output_csv, "r", encoding="utf-8") as f:
            content = f.read()
        # Проверяем, что имена файлов есть (с экранированием для двойных кавычек)
        self.assertIn('some ""quote"".txt', content)
        self.assertIn("John's file.txt", content)
        self.assertIn("Annual report.pdf", content)
        self.assertIn("Пример_файл🙂.txt", content)


if __name__ == "__main__":
    unittest.main()
