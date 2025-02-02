import os
import argparse
import tempfile
from .logger import logger, log_execution


@log_execution(level="DEBUG", message="Нормализация пути")
def normalize_path(path: str) -> str:
    """
    Приводит путь к файлу к каноническому виду (абсолютный и нормализованный).
    :param path: Путь к файлу.
    :type str:
    :return: Нормализованный путь к файлу.
    :rtype str:
    """
    return os.path.normpath(os.path.abspath(path))


@log_execution(level="DEBUG", message="Получение информации о файле")
def get_file_info(filepath: str) -> dict:
    """
    Возвращает словарь с информацией о файле: нормализованный путь и размер.
    Использует существующую функцию normalize_path, если она есть.
    :param filepath: Путь к файлу.
    :type str: Путь к файлу.
    :return: Словарь с информацией о файле.
    :rtype: dict
    """
    normalized = normalize_path(filepath)
    try:
        size = os.path.getsize(filepath)
    except Exception as e:
        size = None
    return {'path': normalized, 'size': size}


@log_execution(level="DEBUG", message="Проверка поддержки символических ссылок")
def check_symlink_support():
    """
    Проверяет, поддерживает ли система символические ссылки.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        test_link = os.path.join(temp_dir, "test_symlink")
        test_target = os.path.join(temp_dir, "test_target")
        try:
            os.symlink(test_target, test_link)
            logger.debug("Символические ссылки поддерживаются системой.")
            return True
        except (OSError, AttributeError, NotImplementedError) as e:
            logger.warning(f"Символические ссылки не поддерживаются: {e}")
            return False


@log_execution(level="DEBUG", message="Проверка директории")
def validate_directory(path):
    """
    Проверяет, существует ли директория и доступна ли она для чтения.
    """
    logger.debug(f"Проверка директории: {path}")
    if not os.path.isdir(path):
        logger.error(f"Директория не существует: {path}")
        raise NotADirectoryError(f"Директория не существует: {path}")
    if not os.access(path, os.R_OK):
        logger.warning(f"Нет доступа к директории: {path}")
        raise PermissionError(f"Нет доступа к директории: {path}")
    logger.debug(f"Директория проверена успешно: {path}")
    return True


@log_execution(level="DEBUG", message="Проверка существования файла")
def check_file_exists(filepath):
    """
    Проверяет, существует ли файл.
    """
    logger.debug(f"Проверка существования файла: {filepath}")
    if not os.path.exists(filepath):
        logger.error(f"Файл не найден: {filepath}")
        raise FileNotFoundError(f"Файл не найден: {filepath}")
    logger.debug(f"Файл существует: {filepath}")


@log_execution(level="DEBUG", message="Проверка доступности файла для чтения")
def check_file_readable(filepath):
    """
    Проверяет, доступен ли файл для чтения.
    """
    logger.debug(f"Проверка доступности файла для чтения: {filepath}")
    if not os.access(filepath, os.R_OK):
        logger.warning(f"Нет доступа к файлу для чтения: {filepath}")
        raise PermissionError(f"Нет доступа к файлу: {filepath}")
    logger.debug(f"Файл доступен для чтения: {filepath}")


@log_execution(level="DEBUG", message="Парсинг аргументов командной строки")
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Поиск дубликатов файлов с гибкими настройками.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--directory", required=True, help="Директория для сканирования")
    parser.add_argument("--exclude", nargs="*", default=[], help="Шаблоны для исключения файлов/директорий")
    parser.add_argument("--hash-type", default="blake3", choices=["md5", "sha1", "sha256", "sha512", "blake3"],
                        help="Алгоритм хэширования (по умолчанию Blake3)")
    parser.add_argument("--output", default="duplicates.csv", help="Имя выходного файла")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Уровень логирования")
    parser.add_argument("--skip-inaccessible", action="store_true",
                        help="Пропускать файлы и директории, к которым нет доступа")
    parser.add_argument("--include-hidden", action="store_true",
                        help="Включать скрытые файлы при сканировании")

    args = parser.parse_args()
    logger.debug(f"Аргументы успешно распознаны: {args}")
    return args


def handle_error(e, context=""):
    """
    Логирует и обрабатывает ошибки.
    """
    error_message = f"{context} — {str(e)}"
    logger.error(error_message)
    return error_message


def human_readable_size(size_in_bytes):
    """
    Преобразует размер файла в удобочитаемый формат.
    """
    if size_in_bytes == 0:
        return "0B"
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while size_in_bytes >= 1024 and index < len(units) - 1:
        size_in_bytes /= 1024
        index += 1
    readable_size = f"{size_in_bytes:.2f}{units[index]}"
    logger.debug(f"Преобразованный размер: {readable_size} для исходного размера {size_in_bytes} байт")
    return readable_size
