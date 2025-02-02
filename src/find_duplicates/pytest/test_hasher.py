import os
import hashlib
import re
import pytest
from find_duplicates.modules.hasher import compute_hash, compute_hash_parallel

try:
    import blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


# Параметризованные тесты для проверки корректного вычисления хэша
@pytest.mark.parametrize("name, hash_type, content, expected", [
    # Тестируем md5 для маленького файла
    ("small_md5", "md5", b"Hello World", hashlib.md5(b"Hello World").hexdigest()),
    # Тестируем sha256 для маленького файла
    ("small_sha256", "sha256", b"Hello World", hashlib.sha256(b"Hello World").hexdigest()),
    # Тестируем sha512 для маленького файла
    ("small_sha512", "sha512", b"Hello World", hashlib.sha512(b"Hello World").hexdigest()),
    # Тестируем md5 для пустого файла
    ("empty_md5", "md5", b"", hashlib.md5(b"").hexdigest()),
    # Тестируем sha256 для пустого файла
    ("empty_sha256", "sha256", b"", hashlib.sha256(b"").hexdigest()),
    # Тестируем sha256 для файла с Unicode-содержимым
    ("unicode_content", "sha256", "Привет мир".encode("utf-8"),
     hashlib.sha256("Привет мир".encode("utf-8")).hexdigest()),
    # Тестируем sha256 для бинарных данных – если expected==None, проверяем по regex
    ("binary_data", "sha256", os.urandom(128), None),
])
def test_compute_hash_valid(tmp_path, name, hash_type, content, expected):
    # Создаем временный файл
    file_path = tmp_path / f"{name}.bin"
    file_path.write_bytes(content)
    result = compute_hash(str(file_path), hash_type)
    if expected is not None:
        assert result == expected
    else:
        # Проверка, что результат содержит только цифры и буквы от a до f
        assert re.match(r"^[0-9a-f]+$", result)


# Тесты для обработки ошибок: несуществующий файл или неверный тип хэша
@pytest.mark.parametrize("name, hash_type, expected_error", [
    ("nonexistent_file", "md5", "Error: File not found"),
    ("invalid_hash", "invalid", "Error"),
])
def test_compute_hash_errors(tmp_path, name, hash_type, expected_error):
    file_path = tmp_path / f"{name}.bin"
    result = compute_hash(str(file_path), hash_type)
    assert expected_error in result


# Тест для алгоритма blake3, если он установлен
@pytest.mark.skipif(not BLAKE3_AVAILABLE, reason="BLAKE3 not installed")
@pytest.mark.parametrize("name, hash_type, content", [
    ("small_blake3", "blake3", b"Hello World"),
])
def test_compute_hash_blake3(tmp_path, name, hash_type, content):
    file_path = tmp_path / f"{name}.bin"
    file_path.write_bytes(content)
    expected = blake3.blake3(content).hexdigest()
    result = compute_hash(str(file_path), hash_type)
    assert result == expected


# Параметризованный тест для параллельного хэширования
@pytest.mark.parametrize("file_keys, hash_type, content, expected_list", [
    (["file1", "file2"], "md5", b"Test", [hashlib.md5(b"Test").hexdigest()] * 2),
    (["missing_file", "file1"], "md5", b"Test",
     ["Error: File not found", hashlib.md5(b"Test").hexdigest()]),
])
def test_compute_hash_parallel(tmp_path, file_keys, hash_type, content, expected_list):
    filepaths = {}
    for key in file_keys:
        path_ = tmp_path / f"{key}.txt"
        if "missing" not in key:
            path_.write_bytes(content)
        filepaths[key] = str(path_)
    results = compute_hash_parallel(list(filepaths.values()), hash_type, num_threads=2)
    for key, path_ in filepaths.items():
        expected = expected_list[file_keys.index(key)]
        if "Error: File not found" in expected:
            assert "Error: File not found" in results[path_]
        else:
            assert results[path_] == expected


# Отдельные тесты для сценариев, где параметризация нецелесообразна

def test_changed_content(tmp_path):
    # Тест: изменение содержимого файла должно приводить к разным хэшам
    file_path = tmp_path / "change.txt"
    file_path.write_bytes(b"Original content")
    hash1 = compute_hash(str(file_path), "md5")
    file_path.write_bytes(b"Modified content")
    hash2 = compute_hash(str(file_path), "md5")
    assert hash1 != hash2


def test_non_readable_file(tmp_path):
    # Тест: файл без прав на чтение должен вернуть сообщение об ошибке
    file_path = tmp_path / "non_readable.bin"
    file_path.write_bytes(b"Secret data")
    os.chmod(str(file_path), 0o000)  # Убираем права на чтение
    result = compute_hash(str(file_path), "md5")
    assert "Permission denied" in result
    os.chmod(str(file_path), 0o644)  # Восстанавливаем права для очистки


def test_custom_block_size(tmp_path):
    # Тест: вычисление хэша с нестандартным размером блока
    file_path = tmp_path / "custom_block.bin"
    data = b"A" * 1024  # 1 КБ данных
    file_path.write_bytes(data)
    result = compute_hash(str(file_path), "md5", block_size=100)
    expected = hashlib.md5(data).hexdigest()
    assert result == expected


def test_large_file(tmp_path):
    # Тест: очень большой файл (5 МБ) должен корректно обрабатываться
    file_path = tmp_path / "large.bin"
    size = 5 * 1024 * 1024
    data = os.urandom(size)
    file_path.write_bytes(data)
    result = compute_hash(str(file_path), "sha256")
    expected = hashlib.sha256(data).hexdigest()
    assert result == expected


def test_special_filename(tmp_path):
    # Тест: имя файла со спецсимволами
    special_name = "spécial_файл!.txt"
    file_path = tmp_path / special_name
    file_path.write_bytes(b"Special content")
    expected = hashlib.md5(b"Special content").hexdigest()
    result = compute_hash(str(file_path), "md5")
    assert result == expected


def test_nonascii_directory(tmp_path):
    # Тест: файл в директории с non‑ASCII именем
    nonascii_dir = tmp_path / "директория"
    nonascii_dir.mkdir()
    file_path = nonascii_dir / "file.txt"
    file_path.write_bytes(b"Data in non-ASCII dir")
    expected = hashlib.sha256(b"Data in non-ASCII dir").hexdigest()
    result = compute_hash(str(file_path), "sha256")
    assert result == expected


def test_parallel_non_readable(tmp_path):
    # Тест: параллельное хэширование с одним файлом недоступным для чтения
    file1 = tmp_path / "accessible.txt"
    file2 = tmp_path / "non_readable.txt"
    file1.write_bytes(b"Test data")
    file2.write_bytes(b"Secret")
    os.chmod(str(file2), 0o000)
    results = compute_hash_parallel([str(file1), str(file2)], "md5", num_threads=2)
    assert results[str(file1)] == hashlib.md5(b"Test data").hexdigest()
    assert "Permission denied" in results[str(file2)]
    os.chmod(str(file2), 0o644)
