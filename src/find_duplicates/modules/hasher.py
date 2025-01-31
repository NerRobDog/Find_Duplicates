import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


def compute_hash(filepath: str, hash_type: str = "blake3", block_size: int = 16 * 1024 * 1024) -> str:
    """
    Вычисляет хэш файла потоково, минимизируя нагрузку на оперативную память.

    :param filepath: Путь к файлу.
    :param hash_type: Алгоритм хэширования (md5, sha256, sha512, blake3).
    :param block_size: Размер блока для чтения (по умолчанию 16MB).
    :return: Хэш файла или сообщение об ошибке.
    :rtype: Str
    """
    if not os.path.exists(filepath):
        return f"Error: File not found: {filepath}"

    try:
        if hash_type == "blake3":
            if not BLAKE3_AVAILABLE:
                return "Error: BLAKE3 not installed"
            hasher = blake3.blake3()
        else:
            hasher = hashlib.new(hash_type)

        with open(filepath, "rb") as f:
            while chunk := f.read(block_size):
                hasher.update(chunk)

        return hasher.hexdigest()

    except PermissionError:
        return f"Error: Permission denied: {filepath}"
    except OSError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: Unexpected error: {str(e)}"


def compute_hash_parallel(filepaths: list, hash_type: str = "blake3", num_threads: int = 4) -> dict:
    """
    Вычисляет хэши нескольких файлов параллельно.

    :param filepaths: Список путей к файлам.
    :param hash_type: Алгоритм хэширования.
    :param num_threads: Количество потоков для обработки.
    :return: Словарь {путь к файлу: хэш или ошибка}.
    :rtype: Dict
    """
    results = {}

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_file = {executor.submit(compute_hash, filepath, hash_type): filepath for filepath in filepaths}

        for future in as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                results[filepath] = future.result()
            except Exception as e:
                results[filepath] = f"Error: {e}"

    return results
