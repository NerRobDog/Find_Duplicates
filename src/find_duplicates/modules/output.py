import csv
from colorama import Fore, Style
from .utils import human_readable_size
from .logger import logger


def write_duplicates_to_csv(duplicates, output_file):
    """
    Записывает найденные дубликаты в CSV-файл.
    Ожидается, что duplicates имеет формат:
      { хэш: [ {'path': <нормализованный путь>, 'size': <размер>}, ... ] }
    """
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Группа", "Путь", "Размер"])
            for group_id, files in sorted(duplicates.items()):
                for idx, file_info in enumerate(files):
                    path = file_info['path']
                    size = file_info['size']
                    hr_size = human_readable_size(size) if size is not None else "N/A"
                    writer.writerow([group_id if idx == 0 else "", path, hr_size])
        logger.info(f"Данные успешно записаны в файл: {output_file}")
        return True
    except (OSError, IOError) as e:
        logger.error(f"Ошибка записи в файл '{output_file}': {e}")
        raise Exception(f"Ошибка записи в CSV: {e}")


def print_tree_view(duplicates):
    for group_id, files in enumerate(duplicates.values(), start=1):
        print(f"{Fore.BLUE}{Style.BRIGHT}Группа {group_id}:{Style.RESET_ALL}")
        for idx, file_info in enumerate(files):
            prefix = "└──" if idx == len(files) - 1 else "├──"
            path = f"{Fore.GREEN}{file_info['path']}{Style.RESET_ALL}"
            size = f"{Fore.YELLOW}{human_readable_size(file_info['size'])}{Style.RESET_ALL}"
            print(f"  {prefix} {path} ({size})")


def save_tree_to_txt(duplicates, output_file):
    with open(output_file, mode='w', encoding='utf-8') as file:
        for group_id, files in enumerate(duplicates.values(), start=1):
            file.write(f"Группа {group_id}:\n")
            for idx, file_info in enumerate(files):
                prefix = "└──" if idx == len(files) - 1 else "├──"
                path = file_info['path']
                size = human_readable_size(file_info['size'])
                file.write(f"  {prefix} {path} ({size})\n")
