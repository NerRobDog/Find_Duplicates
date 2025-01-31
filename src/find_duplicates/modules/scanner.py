import os
from os import walk, path
from fnmatch import fnmatch
import tempfile

"""
walk возвращает список всех файлов и директорий в заданной директории
path возвращает абсолютный путь к файлу или директории
fnmatch используется для сравнения строк с шаблонами
"""


# Проверяем, поддерживает ли система символические ссылки
def check_symlink_support():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_link = path.join(temp_dir, "test_symlink")
        test_target = path.join(temp_dir, "test_target")
        try:
            os.symlink(test_target, test_link)
            return True
        except (OSError, AttributeError, NotImplementedError):
            return False


symlink_supported = check_symlink_support()


def scan_directory(directory, exclude=None, include_hidden=False, follow_symlinks=False) -> list:
    """
    Обходит директорию рекурсивно и возвращает список файлов.

    :param directory: Путь к директории для обхода.
    :type directory: Str
    :param exclude: Список паттернов для исключения файлов и директорий.
    :type exclude: List, optional
    :param include_hidden: Включать скрытые файлы в результат.
    :type include_hidden: Bool, optional
    :param follow_symlinks: Следовать ли за символическими ссылками (по умолчанию False).
    :type follow_symlinks: Bool, optional
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

    for root, dirs, files in walk(directory, followlinks=follow_symlinks if symlink_supported else False):
        # Фильтруем скрытые директории и файлы если include_hidden=False
        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files[:] = [f for f in files if not f.startswith('.')]

        # Обрабатываем файлы
        for name in files:
            full_path = path.join(root, name)

            # Проверяем доступность файла
            if not os.access(full_path, os.R_OK):  # Если нет прав на чтение, исключаем файл
                continue

            # Проверяем, является ли это символической ссылкой
            if os.path.islink(full_path):
                if not follow_symlinks:
                    continue  # Пропускаем симлинк, если follow_symlinks=False
                if not symlink_supported:
                    continue  # Пропускаем, если система не поддерживает симлинки

            # Получаем относительный путь от базовой директории
            relative_path = path.relpath(full_path, base_directory)
            if not is_excluded(relative_path, exclude):
                file_list.append(relative_path)  # Добавляем файл в список

        # Обработка директорий с правами только для чтения
        for dir_name in dirs:
            full_dir_path = path.join(root, dir_name)
            if not os.access(full_dir_path, os.R_OK):  # Если нет прав на чтение для директории
                continue

            # Проверяем, является ли это символической ссылкой на директорию
            if os.path.islink(full_dir_path):
                if not follow_symlinks:
                    continue  # Пропускаем симлинк, если follow_symlinks=False
                if not symlink_supported:
                    continue  # Пропускаем, если система не поддерживает симлинки

    return file_list


def is_excluded(filepath, exclude_patterns):
    # Проверяем, содержится ли путь в списке исключений
    if exclude_patterns:
        for pattern in exclude_patterns:
            if fnmatch(filepath, pattern):
                return True
    return False
