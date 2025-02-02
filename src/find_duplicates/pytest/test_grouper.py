import os
import pytest
from find_duplicates.modules.grouper import group_files_by_size


def create_file(dir_path, name, content="", binary=False):
    """
    Утилита для создания файла (текстового или бинарного).
    Возвращает абсолютный путь к файлу.
    """
    full_path = os.path.join(dir_path, name)
    if binary:
        with open(full_path, "wb") as f:
            f.write(content if isinstance(content, bytes) else content.encode("utf-8"))
    else:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content if isinstance(content, str) else content.decode("utf-8"))
    return os.path.abspath(full_path)


def test_same_size_files(tmp_path):
    """
    Два файла с одинаковым содержимым должны группироваться.
    """
    file1 = create_file(str(tmp_path), "file1.txt", "Hello")
    file2 = create_file(str(tmp_path), "file2.txt", "Hello")
    grouped = group_files_by_size([file1, file2])
    size = os.path.getsize(file1)
    assert size in grouped, "Группа должна формироваться, если есть >1 файл одного размера"
    assert set(grouped[size]) == {file1, file2}


def test_different_sizes(tmp_path):
    """
    Файлы разного размера не группируются.
    """
    f1 = create_file(str(tmp_path), "f1.txt", "abc")
    f2 = create_file(str(tmp_path), "f2.txt", "abcd")
    grouped = group_files_by_size([f1, f2])
    # Группы формируются только при наличии >1 файла, поэтому ожидаем пустой словарь.
    assert grouped == {}


def test_empty_input(tmp_path):
    """
    Пустой список файлов возвращает пустой словарь.
    """
    grouped = group_files_by_size([])
    assert grouped == {}

def test_nonexistent_files(tmp_path):
    """
    Несуществующие файлы игнорируются.
    Если только один файл существует, группа не формируется.
    """
    existing = create_file(str(tmp_path), "exists.txt", "data")
    missing = os.path.join(str(tmp_path), "missing.txt")
    grouped = group_files_by_size([existing, missing])
    # Так как только один файл существует, группа не формируется.
    assert grouped == {}

def test_directory_instead_of_file(tmp_path):
    """
    Директории передаются, но игнорируются.
    """
    d = os.path.join(str(tmp_path), "subdir")
    os.mkdir(d)
    grouped = group_files_by_size([d])
    assert grouped == {}

def test_file_without_permission(tmp_path):
    """
    Файл без прав доступа не учитывается.
    """
    restricted = create_file(str(tmp_path), "restricted.txt", "secret")
    os.chmod(restricted, 0o000)
    grouped = group_files_by_size([restricted])
    assert grouped == {}
    os.chmod(restricted, 0o644)


def test_binary_files(tmp_path):
    """
    Группировка бинарных файлов с одинаковым размером.
    """
    bin1 = create_file(str(tmp_path), "bin1.bin", content=b"\x00" * 100, binary=True)
    bin2 = create_file(str(tmp_path), "bin2.bin", content=b"\x00" * 100, binary=True)
    grouped = group_files_by_size([bin1, bin2])
    size = os.path.getsize(bin1)
    assert size in grouped
    assert set(grouped[size]) == {bin1, bin2}


def test_text_files(tmp_path):
    """
    Группировка текстовых файлов с одинаковым содержимым.
    """
    t1 = create_file(str(tmp_path), "text1.txt", "Some text data")
    t2 = create_file(str(tmp_path), "text2.txt", "Some text data")
    grouped = group_files_by_size([t1, t2])
    size = os.path.getsize(t1)
    assert size in grouped
    assert len(grouped[size]) == 2


def test_zero_size_file(tmp_path):
    """
    Файл размера 0 байт. Если только один такой файл, группа не формируется.
    """
    empty_file = create_file(str(tmp_path), "empty.txt", "")
    grouped = group_files_by_size([empty_file])
    assert grouped == {}


def test_mixed_sizes(tmp_path):
    """
    Смешанный список: файлы с одинаковым размером группируются, уникальные – нет.
    """
    f1 = create_file(str(tmp_path), "a.txt", "hello")
    f2 = create_file(str(tmp_path), "b.txt", "hello")
    f3 = create_file(str(tmp_path), "c.txt", "world!!!")
    grouped = group_files_by_size([f1, f2, f3])
    size_hello = os.path.getsize(f1)
    size_world = os.path.getsize(f3)
    # Ожидаем, что группа для "hello" формируется, а для "world!!!" – нет (так как один файл)
    assert size_hello in grouped
    assert len(grouped[size_hello]) == 2
    assert size_world not in grouped

def test_same_size_different_directories(tmp_path):
    """
    Файлы с одинаковым содержимым, но в разных папках, группируются вместе.
    """
    d1 = os.path.join(str(tmp_path), "dir1")
    d2 = os.path.join(str(tmp_path), "dir2")
    os.mkdir(d1)
    os.mkdir(d2)
    file1 = create_file(d1, "file.txt", "identical")
    file2 = create_file(d2, "file.txt", "identical")
    grouped = group_files_by_size([file1, file2])
    size = os.path.getsize(file1)
    assert size in grouped
    assert set(grouped[size]) == {file1, file2}

def test_nonascii_filenames(tmp_path):
    """
    Файл с non‑ASCII именем: если только один, то группа не формируется.
    """
    file_path = create_file(str(tmp_path), "файл.txt", "unicode data")
    grouped = group_files_by_size([file_path])
    assert grouped == {}

def test_spaces_in_filename(tmp_path):
    """
    Файл с пробелами в имени: если только один, то группа не формируется.
    """
    file_path = create_file(str(tmp_path), "my file.txt", "space data")
    grouped = group_files_by_size([file_path])
    assert grouped == {}


@pytest.mark.slow
def test_large_number_of_files(tmp_path):
    """
    Масштабируемость: создание большого числа файлов с одинаковым содержимым.
    """
    files = []
    for i in range(150):
        f = create_file(str(tmp_path), f"file_{i}.txt", "scalable")
        files.append(f)
    grouped = group_files_by_size(files)
    size = os.path.getsize(files[0])
    assert size in grouped
    assert len(grouped[size]) == 150


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="Symlinks not supported")
def test_file_symlink(tmp_path):
    """
    Проверяем обработку симлинков.
    Создаем целевой файл через create_file, затем удаляем уже созданный файл для симлинка,
    и создаем симлинк вручную.
    """
    target = create_file(str(tmp_path), "target.txt", "symlink test")
    # Для симлинка мы не хотим создавать его через create_file (поскольку он создаст реальный файл).
    link = os.path.join(str(tmp_path), "link.txt")
    # Если файл link уже существует, удалим его
    if os.path.exists(link):
        os.remove(link)
    os.symlink(target, link)
    grouped = group_files_by_size([target, link])
    size = os.path.getsize(target)
    assert size in grouped
    assert set(grouped[size]) == {target, link}


def test_duplicate_names_in_diff_folders(tmp_path):
    """
    Повторяющиеся имена файлов в разных папках, при одинаковом содержимом, группируются.
    """
    d1 = os.path.join(str(tmp_path), "folder1")
    d2 = os.path.join(str(tmp_path), "folder2")
    os.mkdir(d1)
    os.mkdir(d2)
    f1 = create_file(d1, "common.txt", "duplicate")
    f2 = create_file(d2, "common.txt", "duplicate")
    grouped = group_files_by_size([f1, f2])
    size = os.path.getsize(f1)
    assert size in grouped
    assert set(grouped[size]) == {f1, f2}


def test_return_dict_and_keys(tmp_path):
    """
    Проверяем, что функция возвращает словарь, ключи — int, значения — list[str].
    Если в списке только один файл, группа не формируется.
    """
    f = create_file(str(tmp_path), "check.txt", "content")
    grouped = group_files_by_size([f])
    assert isinstance(grouped, dict)
    # Если только один файл, ожидаем пустой словарь
    assert grouped == {}
