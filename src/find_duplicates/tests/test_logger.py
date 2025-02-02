# Файл: tests/test_logger.py
import os
import unittest
import tempfile
import shutil
import re
from io import StringIO
from unittest.mock import patch
from find_duplicates.modules.logger import LoggerWrapper, log_execution, setup_logger


class TestLoggerWrapper(unittest.TestCase):
    def test_console_output(self):
        """
        Проверяем, что LoggerWrapper генерирует сообщения нужного уровня.
        Используем assertLogs для перехвата сообщений.
        """
        logger_wrapper = LoggerWrapper(name="TestLogger", log_level="DEBUG")
        with self.assertLogs("TestLogger", level="DEBUG") as cm:
            logger_wrapper.debug("Debug message")
            logger_wrapper.info("Info message")
            logger_wrapper.warning("Warning message")
        # assertLogs формирует строки вида: "DEBUG:TestLogger:Debug message"
        output = "\n".join(cm.output)
        self.assertIn("DEBUG:TestLogger:Debug message", output)
        self.assertIn("INFO:TestLogger:Info message", output)
        self.assertIn("WARNING:TestLogger:Warning message", output)

    def test_file_output(self):
        """
        Проверяем, что при указании log_file LoggerWrapper пишет в файл.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = os.path.join(tmp_dir, "test.log")
            logger_wrapper = LoggerWrapper(name="TestLoggerFile", log_level="INFO", log_file=log_file)
            logger_wrapper.info("File log message")
            self.assertTrue(os.path.exists(log_file))
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("File log message", content)

    def test_logger_levels(self):
        """
        Проверяем фильтрацию по уровню: при log_level="WARNING"
        сообщения DEBUG и INFO не должны попадать.
        """
        logger_wrapper = LoggerWrapper(name="LevelsLogger", log_level="WARNING")
        with self.assertLogs("LevelsLogger", level="WARNING") as cm:
            logger_wrapper.debug("Debug hidden")
            logger_wrapper.info("Info hidden")
            logger_wrapper.warning("Warning visible")
            logger_wrapper.error("Error visible")
        messages = cm.output  # строки вида "WARNING:LevelsLogger:Warning visible"
        self.assertNotIn("DEBUG:LevelsLogger:Debug hidden", messages)
        self.assertNotIn("INFO:LevelsLogger:Info hidden", messages)
        self.assertIn("WARNING:LevelsLogger:Warning visible", messages)
        self.assertIn("ERROR:LevelsLogger:Error visible", messages)

    def test_logger_format(self):
        """
        Проверяем, что вывод логгера содержит ожидаемый префикс и сообщение.
        В assertLogs вывод по умолчанию имеет формат "LEVEL:LoggerName:Message".
        """
        logger_wrapper = LoggerWrapper(name="FormatLogger", log_level="INFO")
        with self.assertLogs("FormatLogger", level="INFO") as cm:
            logger_wrapper.info("Format test message")
        output = cm.output[0]
        # Ожидаем строку вида "INFO:FormatLogger:Format test message"
        self.assertTrue(output.startswith("INFO:FormatLogger:"))
        self.assertIn("Format test message", output)

    def test_file_not_writable(self):
        """
        Проверяем, что при недоступном каталоге для записи возникает ошибка.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            locked_dir = os.path.join(tmp_dir, "locked")
            os.mkdir(locked_dir)
            os.chmod(locked_dir, 0o400)  # только чтение
            log_file = os.path.join(locked_dir, "test.log")
            with self.assertRaises(Exception):
                LoggerWrapper(name="LockedLogger", log_level="INFO", log_file=log_file)
            os.chmod(locked_dir, 0o700)

    def test_log_sequence(self):
        """
        Проверяем, что сообщения логгера идут в том же порядке, в каком они вызваны.
        """
        logger_wrapper = LoggerWrapper(name="SequenceLogger", log_level="DEBUG")
        messages = ["First", "Second", "Third"]
        with self.assertLogs("SequenceLogger", level="DEBUG") as cm:
            for msg in messages:
                logger_wrapper.info(msg)
        # По умолчанию assertLogs возвращает записи вида "INFO:SequenceLogger:First", и т.д.
        expected = [f"INFO:SequenceLogger:{msg}" for msg in messages]
        self.assertEqual(cm.output, expected)


class TestLogExecutionDecorator(unittest.TestCase):
    def test_log_execution_success(self):
        """
        Проверяем, что декоратор log_execution логирует начало и завершение функции.
        """

        @log_execution(level="DEBUG", message="Test function")
        def sample_function(x, y):
            return x + y

        with self.assertLogs("FindDuplicatesLogger", level="DEBUG") as cm:
            result = sample_function(2, 3)
        self.assertEqual(result, 5)
        output = "\n".join(cm.output)
        self.assertIn("🚀 Начало: Test function", output)
        self.assertIn("✅ Завершение: Test function", output)

    def test_log_execution_exception(self):
        """
        Если функция выбрасывает исключение, декоратор должен залогировать ошибку.
        """

        @log_execution(level="INFO", message="Func with error")
        def error_function():
            raise ValueError("Oops")

        with self.assertLogs("FindDuplicatesLogger", level="INFO") as cm:
            with self.assertRaises(ValueError):
                error_function()
        output = "\n".join(cm.output)
        self.assertIn("🚀 Начало: Func with error", output)
        self.assertIn("❌ Ошибка в функции error_function", output)
        self.assertTrue("Oops" in output or "ValueError" in output)

if __name__ == "__main__":
    unittest.main()