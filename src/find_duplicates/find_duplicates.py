import argparse
from modules import scanner, grouper, hasher, comparer, output, logger, utils


def main():
    """ Основной модуль для поиска дубликатов файлов """
    # Парсинг аргументов
    args = parse_arguments()

    # Настройка логирования
    logger.setup_logger(args.log_level)

    # Проверка директории
    if not utils.validate_directory(args.directory):
        logging.error(f"Директория '{args.directory}' не найдена или недоступна.")
        return

    # Сканирование и фильтрация файлов
    files = scanner.scan_directory(args.directory, args.exclude)

    # Группировка файлов по размеру
    grouped_files = grouper.group_files_by_size(files)

    # Поиск и подтверждение дубликатов
    duplicates = comparer.find_potential_duplicates(grouped_files, args.hash_type)

    # Запись результатов
    output.write_duplicates_to_csv(duplicates, args.output)

    logging.info(f"✅ Поиск завершен! Результаты сохранены в '{args.output}'.")


if __name__ == "__main__":
    main()
