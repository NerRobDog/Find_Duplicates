import os


def read_file(file_path: str) -> str:
    """Reads and returns the contents of a file.

    Args:
        file_path (str): The path to the file to read.

    Returns:
        str: The contents of the file.
    """
    pass


def write_file(file_path: str, content: str) -> None:
    """Writes content to a file.

    Args:
        file_path (str): The path to the file to write.
        content (str): The content to write to the file.
    """
    pass


def parse_arguments():
    pass


def human_readable_size(size_in_bytes):
    if size_in_bytes == 0:
        return "0B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0

    while size_in_bytes >= 1024 and unit_index < len(units) - 1:
        size_in_bytes /= 1024
        unit_index += 1

    return f"{size_in_bytes:.2f}{units[unit_index]}"


def get_partial_content(filepath, size=16 * 1024 * 1024) -> tuple[bytes, bytes]:
    """
    Возвращает первые и последние байты файла для предварительного сравнения.

    :param filepath: Путь к файлу.
    :type filepath: Str
    :param size: Количество байт для чтения (по умолчанию 16 МБ).
    :type size: Int
    :return: Кортеж (первые байты, последние байты).
    :rtype: Tuple[bytes, bytes]
    """

    with open(filepath, "rb") as f:
        # Читаем первые `size` байт
        start = f.read(size)

        # Читаем последние `size` байт
        f.seek(-size, os.SEEK_END)
        end = f.read(size)

    return start, end
