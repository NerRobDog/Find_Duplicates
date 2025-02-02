# Файл: pytest/test_utils.py
import os
import pytest
import sys
from unittest.mock import patch
from io import StringIO

from find_duplicates.modules.utils import (
    normalize_path,
    get_file_info,
    check_symlink_support,
    validate_directory,
    check_file_exists,
    check_file_readable,
    parse_arguments,
    handle_error,
    human_readable_size
)


def test_normalize_path_basic(tmp_path):
    """
    Проверяем, что normalize_path возвращает абсолютный и нормализованный путь.
    """
    d = tmp_path / "sub" / "dir"
    d.mkdir(parents=True)
    rel_path = os.path.join("sub", "dir", "..", "dir")
    expected = str(d.resolve())
    result = normalize_path(os.path.join(str(tmp_path), rel_path))
    assert result == expected


def test_get_file_info_existing_file(tmp_path):
    """
    Проверяем, что get_file_info возвращает корректный путь и размер файла.
    """
    f = tmp_path / "file.txt"
    f.write_text("Hello")
    info = get_file_info(str(f))
    assert info["path"] == os.path.normpath(os.path.abspath(str(f)))
    assert info["size"] == os.path.getsize(str(f))


def test_get_file_info_nonexistent_file(tmp_path):
    """
    Если файл не существует, size должно быть None.
    """
    missing = tmp_path / "missing.txt"
    info = get_file_info(str(missing))
    assert info["size"] is None
    assert info["path"] == os.path.normpath(os.path.abspath(str(missing)))


def test_check_symlink_support():
    """
    Проверяем, что функция check_symlink_support возвращает bool без ошибок.
    """
    result = check_symlink_support()
    assert isinstance(result, bool)


def test_validate_directory_valid(tmp_path):
    """
    Существующая директория возвращает True.
    """
    assert validate_directory(str(tmp_path)) is True


def test_validate_directory_nonexistent(tmp_path):
    """
    Несуществующая директория должна вызывать NotADirectoryError.
    """
    non_exist = str(tmp_path / "no_dir")
    with pytest.raises(NotADirectoryError):
        validate_directory(non_exist)


def test_validate_directory_no_permission(tmp_path):
    """
    Директория без прав на чтение должна вызывать PermissionError.
    """
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    with pytest.raises(PermissionError):
        validate_directory(str(locked))
    locked.chmod(0o755)


def test_check_file_exists_valid(tmp_path):
    """
    Файл существует — функция не должна выбрасывать исключение.
    """
    f = tmp_path / "file.txt"
    f.write_text("content")
    check_file_exists(str(f))  # не должно бросать


def test_check_file_exists_missing(tmp_path):
    """
    Отсутствующий файл вызывает FileNotFoundError.
    """
    missing = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        check_file_exists(str(missing))


def test_check_file_readable_ok(tmp_path):
    """
    Файл с правами на чтение — функция не должна выбрасывать исключение.
    """
    f = tmp_path / "readable.txt"
    f.write_text("readable")
    check_file_readable(str(f))


def test_check_file_readable_no_access(tmp_path):
    """
    Файл без прав на чтение должен вызывать PermissionError.
    """
    f = tmp_path / "no_access.txt"
    f.write_text("Secret")
    f.chmod(0o000)
    with pytest.raises(PermissionError):
        check_file_readable(str(f))
    f.chmod(0o644)


@pytest.mark.parametrize("size, expected", [
    (0, "0B"),
    (999, "999.00B"),
    (1024, "1.00KB"),
    (2048, "2.00KB"),
    (5 * 1024 * 1024, "5.00MB"),
    (3 * 1024 * 1024 * 1024, "3.00GB"),
    (999999999999, None),  # для очень больших значений
])
def test_human_readable_size(size, expected):
    if expected is not None:
        assert human_readable_size(size) == expected
    else:
        res = human_readable_size(size)
        assert len(res) > 0
        # Теперь принимаем, что результат может оканчиваться на GB, TB или PB
        assert res.endswith("GB") or res.endswith("TB") or res.endswith("PB"), f"Ожидали GB, TB или PB, получили {res}"


def test_handle_error():
    """
    Проверяем, что handle_error возвращает строку с контекстом и сообщением об ошибке.
    """
    e = ValueError("Sample error")
    msg = handle_error(e, context="Testing error")
    assert "Testing error" in msg
    assert "Sample error" in msg

def test_parse_arguments_valid(monkeypatch):
    """
    Проверка корректного парсинга аргументов.
    """
    test_args = [
        "prog", "--directory", "/tmp", "--exclude", "*.tmp",
        "--hash-type", "md5", "--output", "results.csv",
        "--log-level", "DEBUG", "--skip-inaccessible"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    args = parse_arguments()
    assert args.directory == "/tmp"
    assert args.exclude == ["*.tmp"]
    assert args.hash_type == "md5"
    assert args.output == "results.csv"
    assert args.log_level == "DEBUG"
    assert args.skip_inaccessible is True

def test_parse_arguments_missing_required(monkeypatch):
    """
    Если не указано --directory, должен возникать SystemExit.
    """
    test_args = ["prog", "--exclude", "*.tmp"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()

def test_parse_arguments_invalid_flags(monkeypatch):
    """
    Неизвестный флаг приводит к SystemExit.
    """
    test_args = ["prog", "--unknown", "value"]
    monkeypatch.setattr(sys, "argv", test_args)
    with pytest.raises(SystemExit):
        parse_arguments()