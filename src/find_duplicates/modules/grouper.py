import os
import hashlib

""" """


def group_files_by_hash(file_paths: list) -> dict:
    """Группирует файлы по их хешу.

    :param file_paths: Список путей файлов для группировки.
    :type file_paths: List[str]
    :returns: Словарь, где ключи - это хеши файлов, значения - списки файлов с этим хешем.
    :rtype: Dict[str, List[str]]
    """
    if not file_paths:
        print("Пустой список файлов = нет хеша.")
        return {}

    hash_dict = {}
    print("Группировка по хешу пока не реализована")

    return hash_dict


def group_files_by_size(file_list) -> dict:
    """Группирует файлы по их размеру.

    :param file_list: Список файлов для группировки.
    :type file_list: List[str]
    :returns: Словарь, ключи - это размер файлов в байтах, значения - списки файлов с этим размером.
    """
    if not file_list:
        print("Пустой список файлов = нет размера.")
        return {}

    size_dict = {}

    for file in file_list:
        try:
            # Пропускаем директории
            if not os.path.isfile(file):
                continue
            # Проверяем доступ к файлу перед вызовом getsize()
            if not os.access(file, os.R_OK):
                print(f"Нет доступа к файлу {file}, пропускаем.")
                continue

            file_size = os.path.getsize(file)
            if file_size not in size_dict:
                size_dict[file_size] = []
            size_dict[file_size].append(file)

        except FileNotFoundError:
            print(f"Файл {file} не найден.")
        except PermissionError:
            print(f"Нет доступа к файлу {file}, пропускаем.")

    return size_dict
