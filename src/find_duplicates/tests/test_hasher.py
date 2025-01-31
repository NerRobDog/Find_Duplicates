import unittest
import os
import hashlib
from ..modules.hasher import compute_hash

try:
    import blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


class TestHasher(unittest.TestCase):
    def setUp(self):
        self.test_file = "test.txt"
        self.test_content = b"Hello, world!" * 1000  # 12 KB данных
        with open(self.test_file, 'wb') as f:
            f.write(self.test_content)

    def tearDown(self):
        os.remove(self.test_file)

    def test_calculate_hash_md5(self):
        file_hash = compute_hash(self.test_file, hash_type="md5")
        expected = hashlib.md5(self.test_content).hexdigest()
        self.assertEqual(file_hash, expected)

    def test_calculate_hash_sha256(self):
        file_hash = compute_hash(self.test_file, hash_type="sha256")
        expected = hashlib.sha256(self.test_content).hexdigest()
        self.assertEqual(file_hash, expected)

    def test_calculate_hash_sha512(self):
        file_hash = compute_hash(self.test_file, hash_type="sha512")
        expected = hashlib.sha512(self.test_content).hexdigest()
        self.assertEqual(file_hash, expected)

    @unittest.skipUnless(BLAKE3_AVAILABLE, "BLAKE3 не установлен")
    def test_calculate_hash_blake3(self):
        file_hash = compute_hash(self.test_file, hash_type="blake3")
        expected = blake3.blake3(self.test_content).hexdigest()
        self.assertEqual(file_hash, expected)

    def test_empty_file(self):
        empty_file = "empty.txt"
        open(empty_file, 'wb').close()
        file_hash = compute_hash(empty_file)
        self.assertIsInstance(file_hash, str)
        os.remove(empty_file)

    def test_large_file(self):
        large_file = "large.txt"
        with open(large_file, 'wb') as f:
            f.write(os.urandom(10 * 1024 * 1024))  # 10 MB random data
        file_hash = compute_hash(large_file)
        self.assertIsInstance(file_hash, str)
        os.remove(large_file)

    def test_identical_files(self):
        duplicate_file = "duplicate.txt"
        with open(duplicate_file, 'wb') as f:
            f.write(self.test_content)
        self.assertEqual(compute_hash(self.test_file), compute_hash(duplicate_file))
        os.remove(duplicate_file)

    def test_different_files(self):
        different_file = "different.txt"
        with open(different_file, 'wb') as f:
            f.write(b"Different content")
        self.assertNotEqual(compute_hash(self.test_file), compute_hash(different_file))
        os.remove(different_file)

    def test_unicode_filename(self):
        unicode_file = "тестовый_файл.txt"
        with open(unicode_file, 'wb') as f:
            f.write(self.test_content)
        file_hash = compute_hash(unicode_file)
        self.assertEqual(file_hash, compute_hash(self.test_file))
        os.remove(unicode_file)

    def test_file_with_null_bytes(self):
        null_file = "null_bytes.bin"
        with open(null_file, 'wb') as f:
            f.write(b"\x00" * 1024)
        file_hash = compute_hash(null_file)
        self.assertIsInstance(file_hash, str)
        os.remove(null_file)

    def test_non_existent_file(self):
        with self.assertRaises(FileNotFoundError):
            compute_hash("non_existent.txt")

    def test_permission_denied(self):
        restricted_file = "restricted.txt"
        with open(restricted_file, 'wb') as f:
            f.write(self.test_content)
        os.chmod(restricted_file, 0o000)
        try:
            with self.assertRaises(PermissionError):
                compute_hash(restricted_file)
        finally:
            os.chmod(restricted_file, 0o777)
            os.remove(restricted_file)


if __name__ == "__main__":
    unittest.main()