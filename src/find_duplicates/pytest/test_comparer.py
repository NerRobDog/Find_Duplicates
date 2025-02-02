# Файл: pytest/test_comparer.py
import os
import pytest
from find_duplicates.modules.comparer import compare_files, find_potential_duplicates
from find_duplicates.modules.grouper import group_files_by_size


def create_file(dir_path, name, content):
    """
    Утилита для создания текстового файла.
    Возвращает абсолютный путь к файлу.
    """
    full_path = os.path.join(dir_path, name)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full_path)


@pytest.fixture
def big_data():
    """
    Условно "большие" данные для теста больших файлов (~2 МБ).
    """
    return "A" * (2 * 1024 * 1024)


# -------------------- Тесты для compare_files -------------------- #

def test_compare_files_identical_text(tmp_path):
    """
    Сравниваем два текстовых файла с одинаковым содержимым — должны совпасть.
    """
    file1 = create_file(str(tmp_path), "file1.txt", "Hello World")
    file2 = create_file(str(tmp_path), "file2.txt", "Hello World")
    assert compare_files(file1, file2) is True


def test_compare_files_diff(tmp_path):
    """
    Файлы с разным содержимым не совпадают.
    """
    f1 = create_file(str(tmp_path), "a.txt", "abc")
    f2 = create_file(str(tmp_path), "b.txt", "abcd")
    assert compare_files(f1, f2) is False


def test_compare_files_empty(tmp_path):
    """
    Два пустых файла — совпадают.
    """
    e1 = create_file(str(tmp_path), "e1.txt", "")
    e2 = create_file(str(tmp_path), "e2.txt", "")
    assert compare_files(e1, e2) is True


def test_compare_files_one_empty(tmp_path):
    """
    Один файл пустой, другой нет.
    """
    empty = create_file(str(tmp_path), "empty.txt", "")
    not_empty = create_file(str(tmp_path), "not_empty.txt", "data")
    # Ожидаем, что функция вернет False
    assert compare_files(empty, not_empty) is False


def test_compare_files_one_byte_diff(tmp_path):
    """
    Файлы, отличающиеся на 1 байт, должны вернуть False.
    """
    file1 = create_file(str(tmp_path), "file1.txt", "HelloA")
    file2 = create_file(str(tmp_path), "file2.txt", "HelloB")
    assert compare_files(file1, file2) is False


def test_compare_files_large(tmp_path, big_data):
    """
    Сравнение больших файлов (пример ~2 МБ).
    """
    f1 = create_file(str(tmp_path), "big1.txt", big_data)
    f2 = create_file(str(tmp_path), "big2.txt", big_data)
    assert compare_files(f1, f2) is True

def test_compare_files_nonexistent(tmp_path):
    """
    Сравнение с несуществующим файлом – функция должна вернуть False.
    """
    file1 = create_file(str(tmp_path), "file1.txt", "abc")
    missing_file = os.path.join(str(tmp_path), "missing.txt")
    # Вместо возбуждения исключения ожидаем, что compare_files вернет False
    assert compare_files(file1, missing_file) is False

def test_compare_files_permission_error(tmp_path):
    """
    Файл без прав на чтение – функция должна вернуть False.
    """
    f1 = create_file(str(tmp_path), "perm1.txt", "Secret")
    f2 = create_file(str(tmp_path), "perm2.txt", "Secret")
    os.chmod(f2, 0o000)
    # Вместо возбуждения исключения ожидаем False (или специальное сообщение)
    assert compare_files(f1, f2) is False
    os.chmod(f2, 0o644)

def test_compare_files_unicode_filenames(tmp_path):
    """
    Сравнение файлов с non‑ASCII именами при совпадающем содержимом.
    """
    file1 = os.path.join(str(tmp_path), "файл1.txt")
    file2 = os.path.join(str(tmp_path), "файл2.txt")
    with open(file1, "w", encoding="utf-8") as f:
        f.write("Unicode content")
    with open(file2, "w", encoding="utf-8") as f:
        f.write("Unicode content")
    assert compare_files(file1, file2) is True


def test_compare_files_repeat(tmp_path):
    """
    Повторное сравнение одного и того же файла должно вернуть True.
    """
    file1 = create_file(str(tmp_path), "repeat.txt", "Repeat data")
    assert compare_files(file1, file1) is True
    assert compare_files(file1, file1) is True


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="Symlinks not supported")
def test_compare_files_symlink(tmp_path):
    """
    Сравнение файла и симлинка, указывающего на него.
    """
    target = create_file(str(tmp_path), "target.txt", "Symlink test")
    link = os.path.join(str(tmp_path), "link.txt")
    if os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)
    assert compare_files(target, link) is True


# -------------------- Тесты для find_potential_duplicates -------------------- #

def create_small_file(dir_path, name, content):
    """
    Утилита для создания небольшого текстового файла.
    Возвращает абсолютный путь.
    """
    full_path = os.path.join(dir_path, name)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(full_path)


def test_find_potential_duplicates_basic(tmp_path):
    """
    Два файла с одинаковым содержимым + один уникальный.
    Ожидается, что два одинаковых попадут в группу.
    """
    dup1 = create_small_file(str(tmp_path), "dup1.txt", "Duplicate")
    dup2 = create_small_file(str(tmp_path), "dup2.txt", "Duplicate")
    unique = create_small_file(str(tmp_path), "unique.txt", "Unique")
    grouped = group_files_by_size([dup1, dup2, unique])
    duplicates = find_potential_duplicates(grouped, "md5")
    assert isinstance(duplicates, dict)
    found = False
    for hsh, group_items in duplicates.items():
        paths = {item["path"] for item in group_items}
        if {dup1, dup2}.issubset(paths):
            found = True
    assert found, "Файлы dup1 и dup2 должны оказаться в одной группе"


def test_find_potential_duplicates_diff_files(tmp_path):
    """
    Два файла с разным содержимым не должны образовывать группу дубликатов.
    """
    f1 = create_small_file(str(tmp_path), "f1.txt", "Content A")
    f2 = create_small_file(str(tmp_path), "f2.txt", "Content B")
    grouped = group_files_by_size([f1, f2])
    duplicates = find_potential_duplicates(grouped, "md5")
    assert duplicates == {}


def test_find_potential_duplicates_error_handling(tmp_path):
    """
    Если один из файлов отсутствует, функция корректно обрабатывает ситуацию.
    """
    f1 = create_small_file(str(tmp_path), "ok.txt", "Test")
    missing = os.path.join(str(tmp_path), "missing.txt")
    grouped = group_files_by_size([f1, missing])
    duplicates = find_potential_duplicates(grouped, "md5")
    assert isinstance(duplicates, dict)


def test_find_potential_duplicates_same_hash_diff_content(tmp_path):
    """
    Два файла одинакового размера, но разное содержимое – не должны объединяться.
    """
    f1 = create_small_file(str(tmp_path), "coll1.txt", "abc")
    f2 = create_small_file(str(tmp_path), "coll2.txt", "abd")
    grouped = group_files_by_size([f1, f2])
    duplicates = find_potential_duplicates(grouped, "md5")
    assert duplicates == {}


@pytest.fixture
def big_data_for_duplicates():
    return "Z" * (2 * 1024 * 1024)


@pytest.mark.slow
def test_find_potential_duplicates_big_files(tmp_path, big_data_for_duplicates):
    """
    Два больших файла с одинаковым содержимым должны попасть в одну группу.
    """
    f1 = os.path.join(str(tmp_path), "bigA.txt")
    f2 = os.path.join(str(tmp_path), "bigB.txt")
    with open(f1, "w", encoding="utf-8") as fw:
        fw.write(big_data_for_duplicates)
    with open(f2, "w", encoding="utf-8") as fw:
        fw.write(big_data_for_duplicates)
    grouped = group_files_by_size([f1, f2])
    duplicates = find_potential_duplicates(grouped, "sha256")
    assert len(duplicates) == 1
    group_list = list(duplicates.values())[0]
    paths = {item["path"] for item in group_list}
    assert {f1, f2} == paths


def test_find_potential_duplicates_permission_error(tmp_path):
    """
    Если один файл недоступен, группа не формируется.
    """
    ok_file = create_small_file(str(tmp_path), "ok.txt", "some data")
    blocked = create_small_file(str(tmp_path), "blocked.txt", "some data")
    os.chmod(blocked, 0o000)
    grouped = group_files_by_size([ok_file, blocked])
    duplicates = find_potential_duplicates(grouped, "md5")
    assert duplicates == {}
    os.chmod(blocked, 0o644)


def test_find_potential_duplicates_unicode_filename(tmp_path):
    """
    Два файла с Unicode-именами и одинаковым содержимым должны быть сгруппированы.
    """
    f1 = create_small_file(str(tmp_path), "файл1.txt", "Unicode data")
    f2 = create_small_file(str(tmp_path), "файл2.txt", "Unicode data")
    grouped = group_files_by_size([f1, f2])
    duplicates = find_potential_duplicates(grouped, "md5")
    assert len(duplicates) == 1
    group_items = list(duplicates.values())[0]
    paths = {item["path"] for item in group_items}
    assert paths == {f1, f2}


def test_find_potential_duplicates_stability(tmp_path):
    """
    Повторный вызов find_potential_duplicates с одной и той же группировкой должен давать идентичный результат.
    """
    f1 = create_small_file(str(tmp_path), "a.txt", "Duplicate")
    f2 = create_small_file(str(tmp_path), "b.txt", "Duplicate")
    grouped = group_files_by_size([f1, f2])
    d1 = find_potential_duplicates(grouped, "md5")
    d2 = find_potential_duplicates(grouped, "md5")
    assert d1 == d2
