# Файл: pytest/test_logger.py
import os
import pytest
from find_duplicates.modules.logger import LoggerWrapper, log_execution


def test_logger_wrapper_console_output(caplog):
    """
    Проверяем вывод логгера (LoggerWrapper) в консоль на уровне DEBUG
    с помощью фикстуры caplog.
    """
    # Устанавливаем для caplog минимальный уровень 'DEBUG'
    # и логгер с именем "TestLogger", чтобы ловить все сообщения.
    caplog.set_level("DEBUG", logger="TestLogger")

    # Создаём логгер
    logger_wrapper = LoggerWrapper(name="TestLogger", log_level="DEBUG")
    logger_wrapper.debug("Debug message")
    logger_wrapper.info("Info message")
    logger_wrapper.warning("Warning message")

    # Все записанные сообщения доступны через caplog.records
    messages = [record.message for record in caplog.records]
    assert "Debug message" in messages
    assert "Info message" in messages
    assert "Warning message" in messages


def test_logger_wrapper_file_output(tmp_path, caplog):
    """
    Проверяем, что при указании log_file сообщения уходят и в файл,
    и при желании всё ещё доступны через caplog.
    """
    log_file = tmp_path / "test.log"

    # Устанавливаем уровень для caplog
    caplog.set_level("INFO", logger="TestLoggerFile")

    logger_wrapper = LoggerWrapper(
        name="TestLoggerFile", log_level="INFO",
        log_file=str(log_file)
    )
    logger_wrapper.info("File log message")

    # Проверяем, что файл появился и содержит нужный текст
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "File log message" in content

    # Также смотрим, что caplog поймал сообщение
    messages = [r.message for r in caplog.records if r.name == "TestLoggerFile"]
    assert "File log message" in messages


def test_logger_wrapper_levels(caplog):
    """
    Проверяем фильтрацию по уровню: log_level="WARNING"
    => DEBUG/INFO не должны появляться, WARNING/ERROR — да.
    """
    caplog.set_level("DEBUG", logger="TestLoggerLevel")

    logger_wrapper = LoggerWrapper(name="TestLoggerLevel", log_level="WARNING")
    logger_wrapper.debug("Debug hidden")
    logger_wrapper.info("Info hidden")
    logger_wrapper.warning("Warning visible")
    logger_wrapper.error("Error visible")

    # Ловим все сообщения именно от "TestLoggerLevel"
    messages = [r.message for r in caplog.records if r.name == "TestLoggerLevel"]
    # DEBUG и INFO — не должны появляться
    assert "Debug hidden" not in messages
    assert "Info hidden" not in messages
    # WARNING и ERROR — должны
    assert "Warning visible" in messages
    assert "Error visible" in messages


def test_log_execution_decorator_success(caplog):
    """
    Проверяем декоратор @log_execution,
    что логирует начало/завершение выполнения.
    """

    @log_execution(level="DEBUG", message="Test function")
    def sample_function(x, y):
        return x + y

    # Установим уровень для caplog
    caplog.set_level("DEBUG", logger="FindDuplicatesLogger")

    result = sample_function(2, 3)
    assert result == 5

    messages = [r.message for r in caplog.records]
    assert any("🚀 Начало: Test function" in msg for msg in messages)
    assert any("✅ Завершение: Test function" in msg for msg in messages)


def test_log_execution_decorator_exception(caplog):
    """
    Если внутри функции выбрасывается исключение,
    декоратор логирует ошибку.
    """

    @log_execution(level="INFO", message="Func with error")
    def error_function():
        raise ValueError("Oops")

    caplog.set_level("INFO", logger="FindDuplicatesLogger")

    with pytest.raises(ValueError):
        error_function()

    messages = [r.message for r in caplog.records]
    assert any("🚀 Начало: Func with error" in msg for msg in messages)
    # Ошибка: ❌ Ошибка в функции <имя> ...
    assert any("❌ Ошибка в функции error_function" in msg for msg in messages)
    # Можно дополнительно проверить, что содержится текст "Oops" или "ValueError"
    # Но логгер пишет лишь "Oops" (текст исключения),
    # так что можно делать:
    assert any("Oops" in msg for msg in messages)


def test_logger_wrapper_format(caplog):
    """
    Проверка формата строк: YYYY-MM-DD HH:MM:SS [LEVEL] Message
    При желании можно проверить через регулярные выражения.
    """
    caplog.set_level("INFO", logger="CheckFormat")

    logger_wrapper = LoggerWrapper(name="CheckFormat", log_level="INFO")
    logger_wrapper.info("Format test")

    # Смотрим записи именно от "CheckFormat"
    records = [r for r in caplog.records if r.name == "CheckFormat"]
    assert len(records) >= 1
    # Проверим, что в record.created есть timestamp (в float),
    # а record.levelname == 'INFO'
    # Или просто убеждаемся, что record.levelname == 'INFO'
    assert records[0].levelname == 'INFO'
    assert records[0].message == "Format test"


def test_logger_wrapper_file_not_writable(tmp_path, caplog):
    """
    Если каталог недоступен для записи,
    возможно выброс ошибки при создании file_handler,
    либо пропуск, в зависимости от реализации.
    """
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    os.chmod(str(locked_dir), 0o400)  # только чтение
    log_file = locked_dir / "test.log"

    # Попробуем создать логгер
    try:
        # Может сразу упасть в FileHandler,
        # или может отработать, но не писать
        _ = LoggerWrapper(name="LockedLogger", log_level="INFO", log_file=str(log_file))
    except Exception as e:
        # Если выбросится IOError/OSError — тест ок
        pass
    finally:
        os.chmod(str(locked_dir), 0o700)

    # Можно проверить, что каплог поймал warning/error ...
    # Или что файл не создался
    assert not log_file.exists()


def test_logger_wrapper_sequence(caplog):
    """
    Проверяем порядок сообщений.
    caplog.records хранит их в порядке появления.
    """
    caplog.set_level("DEBUG", logger="SequenceLogger")

    logger_wrapper = LoggerWrapper(name="SequenceLogger", log_level="DEBUG")
    messages = ["First", "Second", "Third"]
    for msg in messages:
        logger_wrapper.info(msg)

    # Смотрим все messages от 'SequenceLogger'
    records = [r.message for r in caplog.records if r.name == "SequenceLogger"]
    assert records == messages, f"Порядок должен совпадать: {messages}"
