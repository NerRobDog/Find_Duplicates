import os
from .logger import logger, log_execution
from .utils import get_file_info


@log_execution(level="INFO", message="Группировка файлов по размеру")
def group_files_by_size(file_list: list) -> dict:
    """
    Группирует файлы по их размеру, используя get_file_info для получения нормализованного пути и размера.
    Возвращает словарь, где ключ — размер (в байтах), а значение — список нормализованных путей файлов.
    """
    if not file_list:
        logger.warning("Пустой список файлов.")
        return {}

    size_dict = {}
    for file in file_list:
        try:
            if not os.path.isfile(file):
                logger.debug(f"Пропущен недопустимый файл или директория: {file}")
                continue
            if not os.access(file, os.R_OK):
                logger.warning(f"Нет доступа к файлу {file}.")
                continue
            info = get_file_info(file)
            if info['size'] is not None:
                size_dict.setdefault(info['size'], []).append(info['path'])
        except Exception as e:
            logger.error(f"Ошибка обработки файла {file}: {e}")

    # Исключаем группы с единственным файлом
    filtered_dict = {size: files for size, files in size_dict.items() if len(files) > 1}
    logger.info(f"Найдено {len(filtered_dict)} групп по размеру.")
    return filtered_dict
