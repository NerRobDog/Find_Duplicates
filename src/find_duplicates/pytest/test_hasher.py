import os
import re
import pytest
import hashlib
from find_duplicates.modules.hasher import compute_hash, compute_hash_parallel, get_partial_content

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


@pytest.mark.parametrize("name, hash_type, content, expected", [
    ("small_md5", "md5", b"Hello World", hashlib.md5(b"Hello World").hexdigest()),
    ("small_sha256", "sha256", b"Hello World", hashlib.sha256(b"Hello World").hexdigest()),
    ("small_sha512", "sha512", b"Hello World", hashlib.sha512(b"Hello World").hexdigest()),
    ("empty_md5", "md5", b"", hashlib.md5(b"").hexdigest()),
    ("empty_sha256", "sha256", b"", hashlib.sha256(b"").hexdigest()),
    ("unicode_content", "sha256", "Привет мир".encode("utf-8"),
     hashlib.sha256("Привет мир".encode("utf-8")).hexdigest()),
    ("binary_data", "sha256", os.urandom(128), None),
])
def test_compute_hash_valid(tmp_path, name, hash_type, content, expected):
    """
    Тестируем compute_hash для различных вариантов входных данных (md5, sha256, ...).
    """
    file_path = tmp_path / f"{name}.bin"
    file_path.write_bytes(content)
    result = compute_hash(str(file_path), hash_type)

    if expected is not None:
        assert result == expected
    else:
        # Проверяем, что результат содержит только [0-9a-f]
        assert re.match(r"^[0-9a-f]+$", result)


@pytest.mark.parametrize("name, hash_type, expected_error", [
    ("nonexistent_file", "md5", "Error: File not found"),
    ("invalid_hash", "invalid", "Error"),
])
def test_compute_hash_errors(tmp_path, name, hash_type, expected_error):
    """
    Неверная ситуация: несуществующий файл или неправильно указанный алгоритм хэширования.
    """
    file_path = tmp_path / f"{name}.bin"
    result = compute_hash(str(file_path), hash_type)
    assert expected_error in result


@pytest.mark.skipif(not BLAKE3_AVAILABLE, reason="BLAKE3 not installed")
@pytest.mark.parametrize("name, hash_type, content", [
    ("small_blake3", "blake3", b"Hello World"),
])
def test_compute_hash_blake3(tmp_path, name, hash_type, content):
    """
    Тестирование blake3, если он установлен.
    """
    file_path = tmp_path / f"{name}.bin"
    file_path.write_bytes(content)
    import blake3
    expected = blake3.blake3(content).hexdigest()
    result = compute_hash(str(file_path), hash_type)
    assert result == expected


@pytest.mark.parametrize("file_keys, hash_type, content, expected_list", [
    (["file1", "file2"], "md5", b"Test", [hashlib.md5(b"Test").hexdigest()] * 2),
    (["missing_file", "file1"], "md5", b"Test",
     ["Error: File not found", hashlib.md5(b"Test").hexdigest()]),
])
def test_compute_hash_parallel(tmp_path, file_keys, hash_type, content, expected_list):
    """
    Параллельное хэширование нескольких файлов, включая отсутствующие.
    """
    filepaths = {}
    for key in file_keys:
        path_ = tmp_path / f"{key}.txt"
        if "missing" not in key:
            path_.write_bytes(content)
        filepaths[key] = str(path_)

    results = compute_hash_parallel(list(filepaths.values()), hash_type, num_workers=2)
    for key, path_ in filepaths.items():
        expected = expected_list[file_keys.index(key)]
        if "Error: File not found" in expected:
            assert "Error: File not found" in results[path_]
        else:
            assert results[path_] == expected


def test_changed_content(tmp_path):
    """
    Проверяем, что при изменении содержимого файла его хэш меняется.
    """
    file_path = tmp_path / "change.txt"
    file_path.write_bytes(b"Original content")
    hash1 = compute_hash(str(file_path), "md5")
    file_path.write_bytes(b"Modified content")
    hash2 = compute_hash(str(file_path), "md5")
    assert hash1 != hash2


def test_non_readable_file(tmp_path):
    """
    Файл без прав на чтение должен возвращать предупреждение или None.
    """
    file_path = tmp_path / "no_read.bin"
    file_path.write_bytes(b"Secret data")
    file_path.chmod(0o000)
    result = compute_hash(str(file_path), "md5")
    assert "Permission denied" in result
    file_path.chmod(0o644)


def test_custom_block_size(tmp_path):
    """
    Тест с нестандартным размером блока чтения.
    """
    file_path = tmp_path / "custom.bin"
    data = b"A" * 2048
    file_path.write_bytes(data)
    result = compute_hash(str(file_path), "md5", chunk_size=128)
    expected = hashlib.md5(data).hexdigest()
    assert result == expected


@pytest.mark.slow
def test_large_file(tmp_path):
    """
    Тест на большой файл (5 МБ).
    """
    file_path = tmp_path / "large.bin"
    size = 5 * 1024 * 1024
    data = os.urandom(size)
    file_path.write_bytes(data)

    result = compute_hash(str(file_path), "sha256")
    expected = hashlib.sha256(data).hexdigest()
    assert result == expected


def test_special_filename(tmp_path):
    """
    Файл со спецсимволами в имени.
    """
    special_name = "spécial_файл!.txt"
    file_path = tmp_path / special_name
    file_path.write_bytes(b"Special content")
    expected = hashlib.md5(b"Special content").hexdigest()
    result = compute_hash(str(file_path), "md5")
    assert result == expected


def test_nonascii_directory(tmp_path):
    """
    Файл в директории с non-ASCII именем.
    """
    nonascii_dir = tmp_path / "директория"
    nonascii_dir.mkdir()
    file_path = nonascii_dir / "file.txt"
    file_path.write_bytes(b"Data in non-ASCII dir")
    expected = hashlib.sha256(b"Data in non-ASCII dir").hexdigest()
    result = compute_hash(str(file_path), "sha256")
    assert result == expected


def test_parallel_non_readable(tmp_path):
    """
    Параллельное хэширование с одним файлом без прав доступа.
    """
    file1 = tmp_path / "ok.bin"
    file2 = tmp_path / "no_access.bin"
    file1.write_bytes(b"Test")
    file2.write_bytes(b"Secret")
    file2.chmod(0o000)

    results = compute_hash_parallel([str(file1), str(file2)], "md5", num_workers=2)
    assert results[str(file1)] == hashlib.md5(b"Test").hexdigest()
    assert "Permission denied" in results[str(file2)]
    file2.chmod(0o644)


def test_get_partial_content(tmp_path):
    """
    Тестирование функции get_partial_content
    """
    file_path = tmp_path / "partial.bin"
    data = b"A" * 3000
    file_path.write_bytes(data)

    start, end = get_partial_content(str(file_path), size=1024)
    assert len(start) <= 1024, "Длина начального куска не должна превышать 1024"
    # Так как 3000 < 2*1024, возможно end будет пустым
    # Проверяем, что исключений нет
    assert isinstance(end, bytes)
