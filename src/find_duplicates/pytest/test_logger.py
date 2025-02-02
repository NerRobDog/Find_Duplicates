import os
import re
import pytest
from find_duplicates.modules.logger import setup_logger, log_info


# Фикстура для создания лог-файла и настройки логгера
@pytest.fixture
def log_file(tmp_path):
    file = tmp_path / "test.log"
    setup_logger(str(file))
    return str(file)


@pytest.mark.parametrize("message", [
    "Test message",
    "",
    "Line1\nLine2\nLine3"
])
def test_log_info_messages(log_file, message):
    # Тест: запись различных сообщений
    log_info(message)
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert message in log_content


def test_timestamp_in_log(log_file):
    # Тест: наличие временной метки в записи
    test_message = "Timestamp test"
    log_info(test_message)
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    timestamp_regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    assert re.search(timestamp_regex, log_content)


def test_multiple_messages(log_file):
    # Тест: запись нескольких сообщений подряд
    messages = ["First message", "Second message", "Third message"]
    for msg in messages:
        log_info(msg)
    with open(log_file, "r", encoding="utf-8") as f:
        log_lines = f.readlines()
    for msg in messages:
        assert any(msg in line for line in log_lines)


def test_log_format(log_file):
    # Тест: проверка формата строки лога (временная метка, уровень)
    test_message = "Format test"
    log_info(test_message)
    with open(log_file, "r", encoding="utf-8") as f:
        log_line = f.readline().strip()
    pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[INFO\] .+$"
    assert re.match(pattern, log_line)


def test_logging_exception(log_file):
    # Тест: логирование сообщения об исключении
    try:
        raise ValueError("Test exception")
    except Exception as e:
        log_info(f"Exception occurred: {str(e)}")
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert "Test exception" in log_content


def test_file_not_writable(log_file):
    # Тест: попытка записи в лог-файл, недоступный для записи, должна вызвать ошибку
    os.chmod(log_file, 0o444)
    with pytest.raises(Exception):
        log_info("This should fail")
    os.chmod(log_file, 0o644)


def test_sequence_of_messages(log_file):
    # Тест: последовательность сообщений должна сохраняться в том же порядке
    messages = ["Message 1", "Message 2", "Message 3"]
    for msg in messages:
        log_info(msg)
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    start_index = 0
    for msg in messages:
        index = log_content.find(msg, start_index)
        assert index != -1
        start_index = index
