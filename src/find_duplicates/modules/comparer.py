from .hasher import compute_hash
from .utils import check_file_exists, check_file_readable, handle_error, get_file_info
from .logger import logger, log_execution  # Используем кастомный логгер и декоратор


@log_execution(level="DEBUG", message="Побайтовое сравнение файлов")
def compare_files(file1, file2, chunk_size=4 * 1024 * 1024):
    """
    Сравнивает два файла побайтово.

    Предполагается, что файлы уже прошли проверку на совпадение размера и верификацию хэша.

    :param file1: Путь к первому файлу.
    :param file2: Путь ко второму файлу.
    :param chunk_size: Размер блока для чтения (по умолчанию 4 МБ).
    :return: True, если файлы идентичны, иначе False.
    """
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            while True:
                chunk1 = f1.read(chunk_size)
                chunk2 = f2.read(chunk_size)

                if not chunk1 and not chunk2:
                    # Достигнут конец обоих файлов, и различий не найдено
                    return True

                if chunk1 != chunk2:
                    # Обнаружено различие в содержимом файлов
                    return False

    except (FileNotFoundError, PermissionError) as e:
        logger.warning(f"Ошибка доступа к файлам '{file1}' или '{file2}': {e}")
        return False
    except Exception as e:
        logger.error(f"Неизвестная ошибка при сравнении файлов '{file1}' и '{file2}': {e}")
        return False


@log_execution(level="INFO", message="Поиск потенциальных дубликатов")
def find_potential_duplicates(grouped_files, hash_type='blake3') -> dict:
    """
    Находит потенциальные дубликаты, группируя файлы по хэшу, затем
    используя опорное побайтовое сравнение. Возвращает словарь вида:
    {
        хэш: [ {'path': путь_файла, 'size': размер}, ... ]
    }
    :param grouped_files: Группированные файлы по хэшу
    :type grouped_files: Dict
    :param hash_type: Тип хэша для вычисления (по умолчанию 'blake3')
    :type hash_type: Str
    :return: Словарь дубликатов
    :type duplicates: Dict
    """
    duplicates = {}
    try:
        for size, files in grouped_files.items():
            hash_dict = {}
            for file in files:
                try:
                    check_file_exists(file)
                    check_file_readable(file)
                    file_hash = compute_hash(file, hash_type)
                    if file_hash:
                        hash_dict.setdefault(file_hash, []).append(file)
                except Exception as file_error:
                    logger.error(f"Ошибка при обработке файла {file}: {file_error}")
                    handle_error(file_error)

            for file_hash, file_group in hash_dict.items():
                if len(file_group) > 1:
                    confirmed_duplicates = []
                    while file_group:
                        ref_file = file_group.pop(0)
                        group_entry = [get_file_info(ref_file)]
                        non_duplicates = []
                        for other_file in file_group:
                            if compare_files(ref_file, other_file):
                                group_entry.append(get_file_info(other_file))
                            else:
                                non_duplicates.append(other_file)
                        file_group = non_duplicates
                        if len(group_entry) > 1:
                            confirmed_duplicates.extend(group_entry)
                    if confirmed_duplicates:
                        duplicates[file_hash] = confirmed_duplicates
                        logger.debug(f"Найдены дубликаты с хэшем {file_hash}: {confirmed_duplicates}")
        return duplicates
    except Exception as e:
        logger.critical(f"Критическая ошибка при поиске дубликатов: {e}")
        handle_error(e)
        return {}
