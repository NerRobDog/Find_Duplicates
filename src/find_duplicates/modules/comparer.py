import logging

from .hasher import compute_hash
from .utils import get_file_info
from .logger import logger, log_execution


@log_execution(level="DEBUG", message="Побайтовое сравнение двух файлов")
def compare_files(file1, file2, chunk_size=4 * 1024 * 1024):
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            logging.info(f"Сравниваем файлы '{file1}' и '{file2}'")
            while True:
                chunk1 = f1.read(chunk_size)
                chunk2 = f2.read(chunk_size)
                if not chunk1 and not chunk2:
                    return True
                if chunk1 != chunk2:
                    return False
    except Exception as e:
        logger.error(f"Ошибка при сравнении файлов '{file1}' и '{file2}': {e}")
        return False


@log_execution(level="DEBUG", message="Группировка файлов по хэшу")
def group_by_hash(files, hash_type='blake3'):
    """
    Вычисляет хэш для каждого файла и группирует файлы по полученному значению.
    """
    hash_dict = {}
    for file in files:
        h = compute_hash(file, hash_type)
        if h:
            hash_dict.setdefault(h, []).append(file)
    return hash_dict


@log_execution(level="DEBUG", message="Побайтовая верификация группы файлов")
def verify_by_byte(files):
    """
    Сравнивает файлы из списка побайтово, возвращая список информации о подтверждённых дубликатах.
    """
    confirmed = []
    files_copy = files.copy()
    while files_copy:
        ref = files_copy.pop(0)
        entry = [get_file_info(ref)]
        non_dup = []
        for other in files_copy:
            if compare_files(ref, other):
                entry.append(get_file_info(other))
            else:
                non_dup.append(other)
        files_copy = non_dup
        if len(entry) > 1:
            confirmed.extend(entry)
    return confirmed


@log_execution(level="DEBUG", message="Поиск потенциальных дубликатов")
def find_potential_duplicates(files, hash_type='blake3'):
    """
    Для списка файлов сначала группирует по хэшу, затем выполняет побайтовую верификацию для подтверждения.
    Возвращает словарь вида:
      { hash: [ { 'path': <нормализованный путь>, 'size': <размер> }, ... ], ... }
    """
    duplicates = {}
    hash_groups = group_by_hash(files, hash_type)
    for h, group in hash_groups.items():
        if len(group) < 2:
            continue
        verified = verify_by_byte(group)
        if verified:
            duplicates[h] = verified
    return duplicates
