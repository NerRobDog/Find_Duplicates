import os
from fnmatch import fnmatch
from .logger import logger, log_execution


@log_execution(level="DEBUG", message="Сканирование директории")
def scan_directory(directory, include_hidden=False, skip_inaccessible=False, exclude=None) -> list:
    """
    Обходит директорию рекурсивно и возвращает список файлов.

    :param directory: Путь к директории для обхода.
    :type directory: Str
    :param include_hidden: Включать скрытые файлы в результат.
    :type include_hidden: Bool
    :param skip_inaccessible: Пропускать файлы и папки без доступа.
    :type skip_inaccessible: Bool
    :param exclude: Список регулярных выражений для исключения файлов.
    :type exclude: List[str]
    :return: Список файлов.
    :rtype: List[str]
    """
    file_list = []
    exclude = exclude or []

    def scan(dir_path):
        try:
            with os.scandir(dir_path) as entries:
                for entry in entries:
                    # 1) Скрытые файлы, если include_hidden=False, пропускаем
                    if not include_hidden and entry.name.startswith('.'):
                        continue

                    # 2) Проверяем, не указано ли имя (директории или файла) в exclude
                    if is_excluded(entry.path, exclude):
                        logger.debug(f"'{entry.path}/{entry.name}' исключён по шаблонам")
                        continue
                    if is_excluded(entry.name, exclude):
                        logger.debug(f"'{entry.name}' исключён по шаблонам")
                        continue

                    # 3) Проверка доступа
                    if not os.access(entry.path, os.R_OK):
                        msg = f"Нет доступа к {'директории' if entry.is_dir(follow_symlinks=False) else 'файлу'}: {entry.path}"
                        if skip_inaccessible:
                            logger.warning(msg + " — пропускаем.")
                            continue
                        else:
                            raise PermissionError(msg)

                    # 4) Если это директория, рекурсивно заходим в неё
                    if entry.is_dir(follow_symlinks=False):
                        scan(entry.path)
                    # 5) Если это файл — добавляем в список
                    elif entry.is_file(follow_symlinks=False):
                        file_list.append(entry.path)

        except (PermissionError, FileNotFoundError) as e:
            # При skip_inaccessible=True пропускаем
            # иначе выбрасываем, завершая программу
            if skip_inaccessible:
                logger.warning(f"Пропуск недоступного элемента: {e}")
            else:
                logger.error(f"Ошибка доступа: {e}")
                raise

    scan(directory)
    return file_list


@log_execution(level="DEBUG", message="Проверка исключений для файлов и директорий")
def is_excluded(name: str, exclude_patterns: list) -> bool:
    """
    Проверяет, соответствует ли имя файла или директории одному из шаблонов.
    Для директорий можно использовать шаблоны с префиксом 'dir:'.

    :param name: Путь к файлу или директории.
    :type name: Str
    :param exclude_patterns: Список паттернов для исключения.
    :type exclude_patterns: List
    :return: True, если файл должен быть исключён, иначе False.
    :rtype: Bool
    """
    for pattern in exclude_patterns:
        # Используем fnmatch, чтобы проверять соответствие имени и паттерна
        if fnmatch(name, pattern):
            logger.debug(f"Имя '{name}' исключается по шаблону '{pattern}'")
            return True
    return False