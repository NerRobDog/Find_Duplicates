import os
import tempfile
import shutil
import unittest
from parameterized import parameterized
from find_duplicates.modules.logger import setup_logger, log_info

import re


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, "test.log")
        # Инициализируем логгер для записи в файл
        setup_logger(self.log_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @parameterized.expand([
        ("single_message", "Test message"),
        ("empty_message", ""),
        ("multiline_message", "Line1\nLine2\nLine3"),
    ])
    def test_log_info_messages(self, name, message):
        log_info(message)
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
        # Проверяем, что сообщение (даже пустое) присутствует в логе
        self.assertIn(message, log_content)

    def test_timestamp_in_log(self):
        test_message = "Timestamp test"
        log_info(test_message)
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
        # Проверяем, что в строке присутствует временная метка в формате YYYY-MM-DD HH:MM:SS
        timestamp_regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        self.assertRegex(log_content, timestamp_regex)

    def test_multiple_messages(self):
        messages = ["First message", "Second message", "Third message"]
        for msg in messages:
            log_info(msg)
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()
        for msg in messages:
            self.assertTrue(any(msg in line for line in log_lines))

    def test_log_format(self):
        test_message = "Format test"
        log_info(test_message)
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_line = f.readline().strip()
        # Ожидаемый формат, например: "2025-02-01 12:34:56 [INFO] Format test"
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[INFO\] .+$"
        self.assertRegex(log_line, pattern)

    def test_logging_exception(self):
        try:
            raise ValueError("Test exception")
        except Exception as e:
            log_info(f"Exception occurred: {str(e)}")
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
        self.assertIn("Test exception", log_content)

    def test_file_not_writable(self):
        # Делаем лог-файл доступным только для чтения и проверяем обработку ошибки записи
        os.chmod(self.log_file, 0o444)
        with self.assertRaises(Exception):
            log_info("This should fail")
        os.chmod(self.log_file, 0o644)

    def test_sequence_of_messages(self):
        messages = ["Message 1", "Message 2", "Message 3"]
        for msg in messages:
            log_info(msg)
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
        start_index = 0
        for msg in messages:
            index = log_content.find(msg, start_index)
            self.assertNotEqual(index, -1, f"Message '{msg}' not found in order")
            start_index = index


if __name__ == "__main__":
    unittest.main()
