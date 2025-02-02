from modules import scanner, grouper, comparer, output, logger, utils
import logging

logging.root = logger.logger.logger

def main():
    """
    Основной исполняемый модуль для поиска дубликатов файлов.
    Логика:
      1) Парсинг аргументов.
      2) Настройка логгера.
      3) Валидация директории.
      4) Сканирование с учетом флагов.
      5) Группировка по размеру.
      6) Поиск потенциальных дубликатов.
      7) Вывод результатов в CSV.
         Если дубликатов не найдено, создается CSV только с заголовком.
    """
    # 1. Парсинг аргументов
    args = utils.parse_arguments()

    # 2. Настройка логгера
    logger.setup_logger(args.log_level)

    logging.debug(f"Аргументы: {args}")

    # 3. Валидация директории
    try:
        if not utils.validate_directory(args.directory):
            logging.error(f"Директория '{args.directory}' не найдена или недоступна.")
            return
    except Exception as e:
        logging.error(f"Ошибка при проверке директории: {e}")
        return

    # 4. Сканирование директорий (если обнаружена ошибка доступа и флаг не установлен – будет исключение)
    files = scanner.scan_directory(
        directory=args.directory,
        include_hidden=args.include_hidden,
        skip_inaccessible=args.skip_inaccessible,
        exclude=args.exclude
    )
    if not files:
        logging.info("Файлы не найдены в указанной директории.")
        # Создаем CSV с заголовком, чтобы файл существовал
        output.write_duplicates_to_csv({}, args.output)
        return

    # 5. Группировка по размеру
    grouped_files = grouper.group_files_by_size(files)
    if not grouped_files:
        logging.info("Нет групп файлов с одинаковым размером — дубликаты не обнаружены.")
        # Создаем CSV с заголовком
        output.write_duplicates_to_csv({}, args.output)
        return

    # 6. Поиск потенциальных дубликатов
    duplicates = comparer.find_potential_duplicates(grouped_files, args.hash_type)
    if not duplicates:
        logging.info("Дубликаты не обнаружены.")
        # Создаем CSV с заголовком
        output.write_duplicates_to_csv({}, args.output)
        return

    # 7. Вывод результатов в CSV
    if output.write_duplicates_to_csv(duplicates, args.output):
        logging.info(f"Поиск завершён. Результаты сохранены в '{args.output}'.")
    else:
        logging.error("Ошибка при записи результатов в файл CSV.")

if __name__ == "__main__":
    main()