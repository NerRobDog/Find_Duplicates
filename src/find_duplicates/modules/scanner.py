from os import walk, path
import os
from fnmatch import fnmatch

"""
walk возвращает список всех файлов и директорий в заданной директории
path возвращает абсолютный путь к файлу или директории
"""
"""
fnmatch используется для сравнения строк с шаблонами
"""

def scan_directory(directory, exclude=None, include_hidden=False) -> list:
    """
    Обходит директорию рекурсивно и возвращает список файлов.

    :param directory: Путь к директории для обхода.
    :type directory: Str
    :param exclude: Список паттернов для исключения файлов и директорий.
    :type exclude: List, optional
    :param include_hidden: Включать скрытые файлы в результат.
    :type include_hidden: Bool, optional
    :return: Список файлов в указанной директории.
    :rtype: List
    """
    if exclude is None:
        exclude = []

    file_list = []

    # Проверяем, что путь является директорией
    if not os.path.isdir(directory):
        raise OSError(f"{directory} is not a directory")

    # Делаем путь абсолютным
    base_directory = path.abspath(directory)

    for root, dirs, files in walk(directory):
        # Фильтруем скрытые директории и файлы если include_hidden=False
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files[:] = [f for f in files if not f.startswith('.')]

        # Пропускаем файлы по паттерну исключения
        for name in files:
            full_path = path.join(root, name)
            # Проверяем доступность файла
            if not os.access(full_path, os.R_OK):  # Если нет прав на чтение, исключаем файл
                continue

            # Получаем относительный путь от базовой директории
            relative_path = path.relpath(full_path, base_directory)
            if not is_excluded(relative_path, exclude):
                file_list.append(relative_path)  # Добавляем файл в список

    return file_list


def is_excluded(filepath, exclude_patterns):
    # Проверяем, содержится ли путь в списке исключений
    if exclude_patterns:
        for pattern in exclude_patterns:
            if fnmatch(filepath, pattern):
                return True
    return False
