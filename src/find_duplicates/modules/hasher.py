import hashlib
import os
from concurrent.futures import as_completed, ProcessPoolExecutor
from .logger import logger, log_execution
from .utils import handle_error

try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False


@log_execution(level="DEBUG", message="Вычисление хэша файла")
def compute_hash(filepath, hash_type='blake3', chunk_size=4 * 1024 * 1024):
    """
    Вычисляет хэш-сумму файла.

    :param filepath: Путь к файлу.
    :type filepath: str
    :param hash_type: Тип хэша ('md5', 'sha256', 'blake3').
    :type hash_type: str
    :param chunk_size: Размер блока для чтения (по умолчанию 4 МБ).
    :type chunk_size: int
    :return: Хэш-сумма файла или None при ошибке.
    :rtype: str | None
    """
    try:
        if hash_type == 'blake3' and BLAKE3_AVAILABLE:
            hash_func = blake3.blake3()
        else:
            hash_func = hashlib.new(hash_type)

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    except FileNotFoundError:
        logger.warning(f"Ошибка доступа к файлу '{filepath}': Файл не найден")
        return "Error: File not found"  # <-- вместо None
    except PermissionError:
        logger.warning(f"Ошибка доступа к файлу '{filepath}': Permission denied")
        return "Error: Permission denied"  # <-- вместо None
    except Exception as e:
        logger.error(f"Неизвестная ошибка при хэшировании '{filepath}': {e}")
        return f"Error: {str(e)}"  # <-- вместо None


@log_execution(level="DEBUG", message="Параллельное хэширование файлов")
def compute_hash_parallel(filepaths, hash_type='blake3', num_workers=None):
    """
    Параллельное вычисление хэшей для списка файлов.

    :param filepaths: Список путей к файлам.
    :type filepaths: list
    :param hash_type: Тип хэша ('md5', 'sha256', 'blake3').
    :type hash_type: str
    :param num_workers: Количество параллельных процессов (по умолчанию - количество ядер CPU).
    :type num_workers: int
    :return: Словарь с результатами хэширования.
    :rtype: dict
    """
    results = {}

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_file = {executor.submit(compute_hash, filepath, hash_type): filepath for filepath in filepaths}

        for future in as_completed(future_to_file):
            filepath = future_to_file[future]
            try:
                result = future.result()
                if result:
                    results[filepath] = result
                else:
                    logger.warning(f"Не удалось вычислить хэш для файла: {filepath}")
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {filepath}: {e}")

    return results


@log_execution(level="DEBUG", message="Чтение первых и последних байтов файла")
def get_partial_content(filepath, size=16 * 1024 * 1024) -> tuple[bytes, bytes]:
    """
    Возвращает первые и последние байты файла для предварительного сравнения.

    :param filepath: Путь к файлу.
    :param size: Количество байт для чтения (по умолчанию 16 МБ).
    :return: Кортеж (первые байты, последние байты).
    """
    try:
        with open(filepath, "rb") as f:
            start = f.read(size)
            if f.tell() < size:
                return start, b""  # Файл меньше указанного размера

            f.seek(-size, os.SEEK_END)
            end = f.read(size)

        logger.debug(f"Прочитаны первые и последние {size} байт файла {filepath}")
        return start, end

    except Exception as e:
        handle_error(e, context=f"Ошибка при чтении первых и последних байтов файла {filepath}")
        return b"", b""
