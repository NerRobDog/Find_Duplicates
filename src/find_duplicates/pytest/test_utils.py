import os
import sys
import pytest
import re
from find_duplicates.modules.utils import read_file, write_file, parse_arguments, human_readable_size


@pytest.mark.parametrize("content", [
    "Hello World",
    "",
    "Привет мир",
    "Spécial Chåråctęrs: !@#$%^&*()"
])
def test_write_and_read_file(tmp_path, content):
    # Тест: запись и последующее чтение файла
    file = tmp_path / "test.txt"
    write_file(str(file), content)
    read_content = read_file(str(file))
    assert read_content == content


def test_long_content(tmp_path):
    # Тест: работа с длинным контентом
    file = tmp_path / "long.txt"
    content = "A" * 10000
    write_file(str(file), content)
    assert read_file(str(file)) == content


def test_different_newlines(tmp_path):
    # Тест: корректное сохранение переводов строк
    file = tmp_path / "newlines.txt"
    content = "Line1\nLine2\r\nLine3\n"
    write_file(str(file), content)
    assert read_file(str(file)) == content


def test_read_nonexistent_file(tmp_path):
    # Тест: попытка чтения несуществующего файла должна вызвать исключение
    file = tmp_path / "nonexistent.txt"
    with pytest.raises(Exception):
        read_file(str(file))


def test_write_in_inaccessible_path(tmp_path):
    # Тест: попытка записи в недоступный путь
    no_write_dir = tmp_path / "no_write"
    no_write_dir.mkdir()
    os.chmod(str(no_write_dir), 0o444)
    file = no_write_dir / "test.txt"
    with pytest.raises(Exception):
        write_file(str(file), "Content")
    os.chmod(str(no_write_dir), 0o755)


def test_parse_arguments_valid(monkeypatch):
    # Тест: корректная передача аргументов
    test_args = ["prog", "--directory", "/tmp", "--exclude", "*.tmp",
                 "--hash-type", "sha256", "--output", "result.csv", "--log-level", "INFO"]
    monkeypatch.setattr(sys, "argv", test_args)
    args = parse_arguments()
    assert args.directory == "/tmp"
    assert args.exclude == ["*.tmp"]
    assert args.hash_type == "sha256"
    assert args.output == "result.csv"
    assert args.log_level == "INFO"


def test_parse_arguments_missing_required(monkeypatch):
    # Тест: отсутствие обязательных аргументов должно привести к SystemExit
    test_args = ["prog", "--exclude", "*.tmp"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()


def test_parse_arguments_invalid_flags(monkeypatch):
    # Тест: неизвестные флаги приводят к SystemExit
    test_args = ["prog", "--unknown", "value"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()


@pytest.mark.parametrize("size, expected", [
    (0, "0B"),
    (2048, "2.00KB"),
    (5 * 1024 * 1024, "5.00MB"),
    (3 * 1024 * 1024 * 1024, "3.00GB"),
    (1234567890123, None),
])
def test_human_readable_size(size, expected):
    result = human_readable_size(size)
    if expected is not None:
        assert result == expected
    else:
        # Для очень большого значения проверяем наличие TB или PB
        assert isinstance(result, str) and len(result) > 0
        assert re.match(r"^[\d\.]+(TB|PB)$", result)


def test_boundary_cases():
    # Тест: граничные значения для функции human_readable_size
    assert human_readable_size(1023) == "1023.00B"
    assert human_readable_size(1024) == "1.00KB"
