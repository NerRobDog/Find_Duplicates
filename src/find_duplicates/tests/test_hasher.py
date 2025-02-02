import os
import unittest
import tempfile
import shutil
import hashlib
from parameterized import parameterized
from find_duplicates.modules.hasher import compute_hash, compute_hash_parallel, get_partial_content

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


class TestHasherParameterized(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # Параметризованные тесты для простых валидных случаев
    @parameterized.expand([
        ("small_md5", "md5", b"Hello World", hashlib.md5(b"Hello World").hexdigest()),
        ("small_sha256", "sha256", b"Hello World", hashlib.sha256(b"Hello World").hexdigest()),
        ("small_sha512", "sha512", b"Hello World", hashlib.sha512(b"Hello World").hexdigest()),
        ("empty_md5", "md5", b"", hashlib.md5(b"").hexdigest()),
        ("empty_sha256", "sha256", b"", hashlib.sha256(b"").hexdigest()),
        ("unicode_content", "sha256", "Привет Вадич".encode("utf-8"),
         hashlib.sha256("Привет Вадич".encode("utf-8")).hexdigest()),
        ("binary_data", "sha256", os.urandom(128), None),  # если None, проверяем regex
    ])
    def test_compute_hash_valid(self, name, hash_type, content, expected):
        """
        Тестируем compute_hash для различных типов хэшей и контентов.
        """
        file_path = os.path.join(self.test_dir, f"{name}.bin")
        with open(file_path, "wb") as f:
            f.write(content)
        result = compute_hash(file_path, hash_type)

        if expected is not None:
            self.assertEqual(result, expected)
        else:
            # Проверяем, что строка хэша соответствует формату hex
            import re
            self.assertRegex(result, r"^[0-9a-f]+$")

    @parameterized.expand([
        ("nonexistent_file", "md5", "Error: File not found"),
        ("invalid_hash", "invalid", "Error"),
    ])
    def test_compute_hash_errors(self, name, hash_type, expected_error_substr):
        """
        Тестируем сценарии, когда файл не существует или алгоритм хэша неверный.
        """
        file_path = os.path.join(self.test_dir, f"{name}.bin")
        result = compute_hash(file_path, hash_type)
        self.assertIn(expected_error_substr, result)

    @unittest.skipUnless(BLAKE3_AVAILABLE, "BLAKE3 not installed")
    @parameterized.expand([
        ("small_blake3", "blake3", b"Hello World", lambda c: blake3.blake3(c).hexdigest()),
    ])
    def test_compute_hash_blake3(self, name, hash_type, content, expected_func):
        """
        Тестируем алгоритм blake3 (если доступен).
        """
        file_path = os.path.join(self.test_dir, f"{name}.bin")
        with open(file_path, "wb") as f:
            f.write(content)
        expected = expected_func(content)
        result = compute_hash(file_path, hash_type)
        self.assertEqual(result, expected)

    @parameterized.expand([
        ("parallel_all_valid", ["file1", "file2"], "md5", b"Test",
         [hashlib.md5(b"Test").hexdigest()] * 2),
        ("parallel_with_missing", ["missing_file", "file1"], "md5", b"Test",
         ["Error: File not found", hashlib.md5(b"Test").hexdigest()]),
    ])
    def test_compute_hash_parallel(self, case_name, file_keys, hash_type, content, expected_list):
        """
        Параллельное хэширование нескольких файлов, в том числе отсутствующих.
        """
        filepaths = {}
        for key in file_keys:
            path_ = os.path.join(self.test_dir, f"{key}.txt")
            if "missing" not in key:
                with open(path_, "wb") as f:
                    f.write(content)
            filepaths[key] = path_
        results = compute_hash_parallel(list(filepaths.values()), hash_type, num_workers=2)

        for key, path_ in filepaths.items():
            expected = expected_list[file_keys.index(key)]
            if "Error: File not found" in expected:
                self.assertIn("Error: File not found", results[path_])
            else:
                self.assertEqual(results[path_], expected)


class TestHasherAdditional(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_changed_content(self):
        """
        Проверяем, что изменение содержимого файла приводит к разным хэшам.
        """
        file_path = os.path.join(self.test_dir, "change.txt")
        with open(file_path, "wb") as f:
            f.write(b"Original content")
        hash1 = compute_hash(file_path, "md5")
        with open(file_path, "wb") as f:
            f.write(b"Modified content")
        hash2 = compute_hash(file_path, "md5")
        self.assertNotEqual(hash1, hash2)

    def test_non_readable_file(self):
        """
        Файл без прав на чтение должен вернуть сообщение об ошибке.
        """
        file_path = os.path.join(self.test_dir, "no_read.bin")
        with open(file_path, "wb") as f:
            f.write(b"Secret data")
        os.chmod(file_path, 0o000)
        result = compute_hash(file_path, "md5")
        self.assertIn("Permission denied", result)
        os.chmod(file_path, 0o644)

    def test_custom_block_size(self):
        """
        Тест с нестандартным размером блока чтения.
        """
        file_path = os.path.join(self.test_dir, "custom_block.bin")
        data = b"A" * 2048
        with open(file_path, "wb") as f:
            f.write(data)
        result = compute_hash(file_path, "md5", chunk_size=100)
        expected = hashlib.md5(data).hexdigest()
        self.assertEqual(result, expected)

    def test_large_file(self):
        """
        Тест на очень большой файл (5 МБ условно), чтобы убедиться, что алгоритм работает корректно.
        """
        file_path = os.path.join(self.test_dir, "large.bin")
        size = 5 * 1024 * 1024
        data = os.urandom(size)
        with open(file_path, "wb") as f:
            f.write(data)
        result = compute_hash(file_path, "sha256")
        expected = hashlib.sha256(data).hexdigest()
        self.assertEqual(result, expected)

    def test_special_filename(self):
        """
        Тест с именем файла, содержащим спецсимволы и unicode.
        """
        special_name = "spécial_файл!.txt"
        file_path = os.path.join(self.test_dir, special_name)
        with open(file_path, "wb") as f:
            f.write(b"Special content")
        expected = hashlib.md5(b"Special content").hexdigest()
        result = compute_hash(file_path, "md5")
        self.assertEqual(result, expected)

    def test_nonascii_directory(self):
        """
        Файл в директории с non-ASCII именем.
        """
        nonascii_dir = os.path.join(self.test_dir, "директория")
        os.mkdir(nonascii_dir)
        file_path = os.path.join(nonascii_dir, "file.txt")
        with open(file_path, "wb") as f:
            f.write(b"Data in non-ASCII dir")
        expected = hashlib.sha256(b"Data in non-ASCII dir").hexdigest()
        result = compute_hash(file_path, "sha256")
        self.assertEqual(result, expected)

    def test_parallel_non_readable(self):
        """
        Параллельное хэширование с одним файлом недоступным для чтения.
        """
        file1 = os.path.join(self.test_dir, "accessible.txt")
        file2 = os.path.join(self.test_dir, "no_readable.txt")

        with open(file1, "wb") as f:
            f.write(b"Test data")

        with open(file2, "wb") as f:
            f.write(b"Secret")
        os.chmod(file2, 0o000)

        results = compute_hash_parallel([file1, file2], "md5", num_workers=2)
        self.assertEqual(results[file1], hashlib.md5(b"Test data").hexdigest())
        self.assertIn("Permission denied", results[file2])
        os.chmod(file2, 0o644)


if __name__ == "__main__":
    unittest.main()