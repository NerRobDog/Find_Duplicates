import unittest
import coverage
import os
import hashlib
from tempfile import NamedTemporaryFile
from ..modules.hasher import compute_hash, compute_hash_parallel

try:
    import blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


class TestHasher(unittest.TestCase):
    def setUp(self):
        """Создаёт тестовые файлы с различными размерами и содержимым."""
        self.small_file = NamedTemporaryFile(delete=False)
        self.small_file.write(b"Hello World")
        self.small_file.close()

        self.empty_file = NamedTemporaryFile(delete=False)
        self.empty_file.close()

        self.large_file = NamedTemporaryFile(delete=False)
        self.large_file.write(os.urandom(10 * 1024 * 1024))  # 10MB
        self.large_file.close()

    def tearDown(self):
        """Удаляет тестовые файлы после завершения тестов."""
        for file in [self.small_file.name, self.empty_file.name, self.large_file.name]:
            if os.path.exists(file):
                os.remove(file)

    # --- Тесты для compute_hash ---
    def test_md5_hash(self):
        """Тестирует вычисление MD5 хэша для небольшого файла."""
        expected = hashlib.md5(b"Hello World").hexdigest()
        self.assertEqual(compute_hash(self.small_file.name, "md5"), expected)

    def test_sha256_hash(self):
        """Тестирует вычисление SHA256 хэша для небольшого файла."""
        expected = hashlib.sha256(b"Hello World").hexdigest()
        self.assertEqual(compute_hash(self.small_file.name, "sha256"), expected)

    def test_sha512_hash(self):
        """Тестирует вычисление SHA512 хэша для небольшого файла."""
        expected = hashlib.sha512(b"Hello World").hexdigest()
        self.assertEqual(compute_hash(self.small_file.name, "sha512"), expected)

    @unittest.skipUnless(BLAKE3_AVAILABLE, "BLAKE3 не установлен")
    def test_blake3_hash(self):
        """Тестирует вычисление BLAKE3 хэша для небольшого файла."""
        expected = blake3.blake3(b"Hello World").hexdigest()
        self.assertEqual(compute_hash(self.small_file.name, "blake3"), expected)

    def test_empty_file_hash(self):
        """Тестирует вычисление SHA256 хэша для пустого файла."""
        self.assertEqual(compute_hash(self.empty_file.name, "sha256"), hashlib.sha256(b"").hexdigest())

    def test_large_file_hash(self):
        """Тестирует вычисление MD5 хэша для большого файла (10MB)."""
        result = compute_hash(self.large_file.name, "md5")
        self.assertIsInstance(result, str)

    def test_non_existent_file(self):
        """Тестирует обработку ошибки при попытке хэширования несуществующего файла."""
        self.assertIn("Error: File not found", compute_hash("missing.txt"))

    def test_permission_error(self):
        """Тестирует обработку ошибки доступа (PermissionError)."""
        os.chmod(self.small_file.name, 0o000)  # Запрещаем доступ
        self.assertIn("Error: Permission denied", compute_hash(self.small_file.name))
        os.chmod(self.small_file.name, 0o644)  # Возвращаем доступ

    def test_invalid_hash_type(self):
        """Тестирует обработку ошибки при передаче неверного типа хэширования."""
        self.assertIn("Error", compute_hash(self.small_file.name, "invalid"))

    # --- Тесты для compute_hash_parallel ---
    def test_parallel_hashing(self):
        """Тестирует параллельное хэширование списка файлов."""
        files = [self.small_file.name, self.empty_file.name, self.large_file.name]
        results = compute_hash_parallel(files, "sha256", num_threads=2)
        self.assertEqual(len(results), 3)

    def test_parallel_missing_file(self):
        """Тестирует обработку ошибки при параллельном хэшировании несуществующего файла."""
        results = compute_hash_parallel(["missing.txt"], "sha256")
        self.assertIn("Error: File not found", results["missing.txt"])

    def test_parallel_permission_error(self):
        """Тестирует обработку ошибки доступа (PermissionError) при параллельном хэшировании."""
        os.chmod(self.small_file.name, 0o000)
        results = compute_hash_parallel([self.small_file.name], "sha256")
        self.assertIn("Error: Permission denied", results[self.small_file.name])
        os.chmod(self.small_file.name, 0o644)

    def test_parallel_large_file(self):
        """Тестирует параллельное хэширование большого файла (10MB)."""
        results = compute_hash_parallel([self.large_file.name], "sha256")
        self.assertIsInstance(results[self.large_file.name], str)

    def test_parallel_empty_list(self):
        """Тестирует обработку пустого списка файлов при параллельном хэшировании."""
        results = compute_hash_parallel([], "sha256")
        self.assertEqual(results, {})


import unittest
import coverage
import os

if __name__ == "__main__":
    cov = coverage.Coverage(source=["find_duplicates/modules"])
    cov.start()

    unittest.main()

    cov.stop()
    cov.save()
    cov.html_report(directory="htmlcov")
    os.system("open htmlcov/index.html")  # Открывает браузер
