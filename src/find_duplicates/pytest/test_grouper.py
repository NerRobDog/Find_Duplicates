import os
import pytest
from find_duplicates.modules.grouper import group_files_by_size


# Вспомогательная функция для создания файла
def create_file(tmp_path, filename, content, binary=False):
    file = tmp_path / filename
    if binary:
        file.write_bytes(content)
    else:
        file.write_text(content)
    return str(file)


def test_grouping_same_and_different(tmp_path):
    # Тест: два файла с одинаковым содержимым и один с другим содержимым
    file1 = create_file(tmp_path, "file1_same.txt", "Hello")
    file2 = create_file(tmp_path, "file2_same.txt", "Hello")
    file3 = create_file(tmp_path, "file3_diff.txt", "World!")
    grouped = group_files_by_size([file1, file2, file3])
    expected_size = os.path.getsize(file1)
    # Файлы с одинаковым содержимым должны группироваться вместе
    assert expected_size in grouped
    assert len(grouped[expected_size]) == 2
    size_diff = os.path.getsize(file3)
    assert size_diff in grouped
    assert len(grouped[size_diff]) == 1


def test_empty_list():
    # Тест: пустой список должен вернуть пустой словарь
    assert group_files_by_size([]) == {}


def test_nonexistent_files(tmp_path):
    # Тест: несуществующие файлы игнорируются
    file1 = create_file(tmp_path, "file.txt", "data")
    non_exist = str(tmp_path / "missing.txt")
    grouped = group_files_by_size([file1, non_exist])
    size = os.path.getsize(file1)
    assert size in grouped
    assert grouped[size] == [file1]


def test_directory_instead_of_file(tmp_path):
    # Тест: передача директории вместо файла
    d = tmp_path / "subdir"
    d.mkdir()
    grouped = group_files_by_size([str(d)])
    assert grouped == {}


def test_file_without_permission(tmp_path):
    # Тест: файл без прав доступа не учитывается
    file_path = create_file(tmp_path, "no_access.txt", "restricted")
    os.chmod(file_path, 0o000)
    grouped = group_files_by_size([file_path])
    assert grouped == {}
    os.chmod(file_path, 0o644)


def test_grouping_binary_file(tmp_path):
    # Тест: группировка бинарного файла
    file_path = create_file(tmp_path, "binary.bin", b"\x00" * 256, binary=True)
    grouped = group_files_by_size([file_path])
    size = os.path.getsize(file_path)
    assert size in grouped
    assert grouped[size] == [file_path]


def test_grouping_text_file(tmp_path):
    # Тест: группировка текстового файла
    file_path = create_file(tmp_path, "text.txt", "Some text data")
    grouped = group_files_by_size([file_path])
    size = os.path.getsize(file_path)
    assert size in grouped
    assert grouped[size] == [file_path]


def test_file_size_zero(tmp_path):
    # Тест: файл размера 0
    file_path = create_file(tmp_path, "empty.txt", "")
    grouped = group_files_by_size([file_path])
    assert 0 in grouped
    assert grouped[0] == [file_path]


def test_mixed_list(tmp_path):
    # Тест: смешанный список файлов с одинаковым и разным размером
    file1 = create_file(tmp_path, "a.txt", "same")
    file2 = create_file(tmp_path, "b.txt", "same")
    file3 = create_file(tmp_path, "c.txt", "different")
    grouped = group_files_by_size([file1, file2, file3])
    size_same = os.path.getsize(file1)
    size_diff = os.path.getsize(file3)
    assert size_same in grouped and len(grouped[size_same]) == 2
    assert size_diff in grouped and len(grouped[size_diff]) == 1


def test_same_size_different_directories(tmp_path):
    # Тест: файлы с одинаковым размером, но в разных папках
    d1 = tmp_path / "dir1";
    d2 = tmp_path / "dir2"
    d1.mkdir();
    d2.mkdir()
    file1 = create_file(d1, "file.txt", "identical")
    file2 = create_file(d2, "file.txt", "identical")
    grouped = group_files_by_size([file1, file2])
    size = os.path.getsize(file1)
    assert size in grouped
    assert set(grouped[size]) == {file1, file2}


def test_nonascii_filenames(tmp_path):
    # Тест: файлы с non‑ASCII именами
    file_path = create_file(tmp_path, "файл.txt", "data")
    grouped = group_files_by_size([file_path])
    size = os.path.getsize(file_path)
    assert size in grouped
    assert grouped[size] == [file_path]


def test_spaces_in_filename(tmp_path):
    # Тест: файл с пробелами в имени
    file_path = create_file(tmp_path, "file with spaces.txt", "content")
    grouped = group_files_by_size([file_path])
    size = os.path.getsize(file_path)
    assert size in grouped
    assert grouped[size] == [file_path]


def test_large_number_of_files(tmp_path):
    # Тест: большое число файлов для проверки масштабируемости
    num_files = 50
    files = []
    for i in range(num_files):
        f = create_file(tmp_path, f"file_{i}.txt", "scalable")
        files.append(f)
    grouped = group_files_by_size(files)
    size = os.path.getsize(files[0])
    assert size in grouped
    assert len(grouped[size]) == num_files


def test_file_symlink(tmp_path):
    # Тест: обработка симлинков
    if not hasattr(os, "symlink"):
        pytest.skip("Symlinks not supported")
    target = create_file(tmp_path, "target.txt", "symlink test")
    symlink_path = str(tmp_path / "link.txt")
    os.symlink(target, symlink_path)
    grouped = group_files_by_size([target, symlink_path])
    size = os.path.getsize(target)
    assert size in grouped
    assert set(grouped[size]) == {target, symlink_path}


def test_duplicate_names_in_different_folders(tmp_path):
    # Тест: повторяющиеся имена файлов в разных папках
    d1 = tmp_path / "d1";
    d2 = tmp_path / "d2"
    d1.mkdir();
    d2.mkdir()
    file1 = create_file(d1, "common.txt", "duplicate")
    file2 = create_file(d2, "common.txt", "duplicate")
    grouped = group_files_by_size([file1, file2])
    size = os.path.getsize(file1)
    assert size in grouped
    assert set(grouped[size]) == {file1, file2}


def test_return_type_and_key_value_types(tmp_path):
    # Тест: проверка типа возвращаемого значения и типов ключей/значений
    file1 = create_file(tmp_path, "a.txt", "content")
    file2 = create_file(tmp_path, "b.txt", "different")
    grouped = group_files_by_size([file1, file2])
    assert isinstance(grouped, dict)
    for key, value in grouped.items():
        assert isinstance(key, int)
        assert isinstance(value, list)
        for item in value:
            assert isinstance(item, str)
