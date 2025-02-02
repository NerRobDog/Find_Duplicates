import os
import pytest
import hashlib
from find_duplicates.modules.comparer import compare_files, find_potential_duplicates
from find_duplicates.modules.grouper import group_files_by_size


# Параметризованный тест для текстовых файлов
@pytest.mark.parametrize("content1, content2, expected", [
    ("Hello World", "Hello World", True),
    ("Hello", "World", False),
    ("", "", True),
    ("", "Data", False),
])
def test_compare_files_text(tmp_path, content1, content2, expected):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text(content1)
    file2.write_text(content2)
    result = compare_files(str(file1), str(file2))
    assert result == expected


def test_compare_files_binary(tmp_path):
    # Тест: бинарные файлы с одинаковым содержимым
    file1 = tmp_path / "binary1.bin"
    file2 = tmp_path / "binary2.bin"
    data = os.urandom(1024)
    file1.write_bytes(data)
    file2.write_bytes(data)
    result = compare_files(str(file1), str(file2))
    assert result is True


def test_compare_files_small_difference(tmp_path):
    # Тест: файлы, отличающиеся одной байтовой разницей
    file1 = tmp_path / "diff1.txt"
    file2 = tmp_path / "diff2.txt"
    data1 = b"1234567890"
    data2 = b"1234567891"
    file1.write_bytes(data1)
    file2.write_bytes(data2)
    result = compare_files(str(file1), str(file2))
    assert result is False


def test_compare_files_nonexistent(tmp_path):
    # Тест: один файл не существует – должно вызвать исключение
    file1 = tmp_path / "exists.txt"
    file1.write_text("Data")
    file2 = tmp_path / "nonexistent.txt"
    with pytest.raises(Exception):
        compare_files(str(file1), str(file2))


def test_compare_files_permission_error(tmp_path):
    # Тест: файлы с ошибкой доступа
    file1 = tmp_path / "perm1.txt"
    file2 = tmp_path / "perm2.txt"
    file1.write_text("Secret")
    file2.write_text("Secret")
    os.chmod(str(file2), 0o000)
    with pytest.raises(Exception):
        compare_files(str(file1), str(file2))
    os.chmod(str(file2), 0o644)


def test_compare_files_large(tmp_path):
    # Тест: сравнение больших файлов (1 МБ одинакового содержимого)
    file1 = tmp_path / "large1.txt"
    file2 = tmp_path / "large2.txt"
    data = "A" * (1024 * 1024)
    file1.write_text(data)
    file2.write_text(data)
    result = compare_files(str(file1), str(file2))
    assert result is True


def test_compare_files_unicode_filenames(tmp_path):
    # Тест: файлы с non‑ASCII именами
    file1 = tmp_path / "файл1.txt"
    file2 = tmp_path / "файл2.txt"
    file1.write_text("Unicode content", encoding="utf-8")
    file2.write_text("Unicode content", encoding="utf-8")
    result = compare_files(str(file1), str(file2))
    assert result is True


def test_repeat_comparison(tmp_path):
    # Тест: повторное сравнение одного и того же файла
    file1 = tmp_path / "repeat.txt"
    file1.write_text("Repeat")
    result1 = compare_files(str(file1), str(file1))
    result2 = compare_files(str(file1), str(file1))
    assert result1 is True and result2 is True


def test_compare_files_symlink(tmp_path):
    # Тест: сравнение файла и его симлинка
    if not hasattr(os, "symlink"):
        pytest.skip("Symlinks not supported")
    target = tmp_path / "target.txt"
    target.write_text("Symlink test")
    symlink = tmp_path / "link.txt"
    os.symlink(str(target), str(symlink))
    result = compare_files(str(target), str(symlink))
    assert result is True


def test_stability_multiple_calls(tmp_path):
    # Тест: стабильность при нескольких последовательных вызовах
    file1 = tmp_path / "stable.txt"
    file2 = tmp_path / "stable2.txt"
    file1.write_text("Stable content")
    file2.write_text("Stable content")
    for _ in range(5):
        assert compare_files(str(file1), str(file2)) is True


def test_find_potential_duplicates(tmp_path):
    # Тест: группировка потенциальных дубликатов по хэшу
    file1 = tmp_path / "dup1.txt"
    file2 = tmp_path / "dup2.txt"
    file3 = tmp_path / "unique.txt"
    content_dup = "Duplicate content"
    content_unique = "Unique content"
    file1.write_text(content_dup)
    file2.write_text(content_dup)
    file3.write_text(content_unique)
    grouped = group_files_by_size([str(file1), str(file2), str(file3)])
    duplicates = find_potential_duplicates(grouped, "md5")
    found = any(set(group) == {str(file1), str(file2)} for group in duplicates.values())
    assert found is True


def test_find_duplicates_no_false_positives(tmp_path):
    # Тест: файлы с разным содержимым не должны сгруппироваться вместе
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("Content A")
    file2.write_text("Content B")
    grouped = group_files_by_size([str(file1), str(file2)])
    duplicates = find_potential_duplicates(grouped, "md5")
    for group in duplicates.values():
        assert len(group) < 2


def test_find_duplicates_error_handling(tmp_path):
    # Тест: обработка ошибочных входных данных
    grouped = {"invalid_key": ["nonexistent_file.txt"]}
    try:
        duplicates = find_potential_duplicates(grouped, "md5")
        assert isinstance(duplicates, dict)
    except Exception as e:
        pytest.fail(f"find_potential_duplicates raised an exception: {e}")
