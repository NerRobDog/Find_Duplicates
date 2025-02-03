from modules import scanner, grouper, comparer, output, logger, utils, hasher
import logging, os

logging.root = logger.logger.logger


def main():
    """
    Главный скрипт для поиска дубликатов файлов.
    Выполняет:
      1. Парсинг аргументов.
      2. Настройку логгера.
      3. Валидацию директории.
      4. Сканирование с учётом исключений и скрытых файлов.
      5. Группировку файлов по размеру.
      6. Предварительную фильтрацию с использованием get_partial_content и выбор этапов проверки
         (хэш‑верификация, побайтовое сравнение, параллельное вычисление) – управляется флагами.
      7. Вывод результатов в CSV.
    """
    # 1. Парсинг аргументов
    args = utils.parse_arguments()

    # 2. Настройка логгера
    logger.setup_logger(args.log_level)
    logging.debug(f"Аргументы: {args}")
    logging.info(f"Скрипт запущен.")

    # 3. Валидация директории и сбор файлов
    all_files = []
    # Используем args.directory (список директорий)
    for directory in args.directory:
        try:
            if not utils.validate_directory(directory):
                logging.error(f"Директория '{directory}' не найдена или недоступна.")
                # Если одна из директорий недоступна, пропускаем её, а не завершаем выполнение
                continue
        except Exception as e:
            logging.error(f"Ошибка при проверке директории '{directory}': {e}")
            continue

        # 4. Сканирование текущей директории
        files = scanner.scan_directory(
            directory=directory,
            include_hidden=args.include_hidden,
            skip_inaccessible=args.skip_inaccessible,
            exclude=args.exclude
        )
        all_files.extend(files)
    if not all_files:
        logging.info("Файлы не найдены в указанных директориях.")
        output.write_duplicates_to_csv({}, args.output)
        return

    # 5. Группировка файлов по размеру
    grouped_files = grouper.group_files_by_size(all_files)
    if not grouped_files:
        logging.info("Нет групп файлов с одинаковым размером — дубликаты не обнаружены.")
        output.write_duplicates_to_csv({}, args.output)
        return
    logging.info(f"Найдено {len(grouped_files)} групп файлов с одинаковым размером.")

    # 6. Для каждой группы по размеру: предварительная фильтрация по partial content и выбор этапов проверки
    duplicates = {}
    for size, file_group in grouped_files.items():
        if len(file_group) < 2:
            continue
        # Предварительное разделение по get_partial_content (например, читаем по 1 КБ с начала и конца)
        partial_groups = {}
        for file in file_group:
            try:
                start, end = hasher.get_partial_content(file)
                key = (start, end)
                partial_groups.setdefault(key, []).append(file)
            except Exception as e:
                logging.error(f"Ошибка при получении partial content для {file}: {e}")
                continue
        # logging.info(f"Найдено {len(partial_groups)} частичных групп для размера {size}.")
        for partial_key, partial_group in partial_groups.items():
            if len(partial_group) < 2:
                continue
            # Если отключен этап хэш-верификации
            if args.disable_hash_check:
                # logging.info(f'Верификация отключена.')
                if args.disable_byte_compare:
                    duplicates[f"size_{size}"] = [utils.get_file_info(f) for f in partial_group]
                else:
                    logging.info(f'Проверка по байтам отключена.')
                    verified = comparer.verify_by_byte(partial_group)
                    if verified:
                        duplicates[f"size_{size}"] = verified
            else:
                # Хэш-верификация включена
                if args.parallel:
                    from modules.hasher import compute_hash_parallel
                    workers = args.workers or os.cpu_count()
                    hash_results = compute_hash_parallel(partial_group, args.hash_type, num_workers=workers)
                    hash_groups = {}
                    for file, h in hash_results.items():
                        if h:
                            hash_groups.setdefault(h, []).append(file)
                else:
                    hash_groups = comparer.group_by_hash(partial_group, args.hash_type)
                for h, group in hash_groups.items():
                    if len(group) < 2:
                        continue
                    if args.disable_byte_compare:
                        logging.info(f'Проверка по байтам отключена.')
                        duplicates[h] = [utils.get_file_info(f) for f in group]
                    else:
                        logging.info(f'Проверка по байтам группы {h}:')
                        verified = comparer.verify_by_byte(group)
                        if verified:
                            duplicates[h] = verified

    if not duplicates:
        logging.info("Дубликаты не обнаружены.")
        output.write_duplicates_to_csv({}, args.output)
        return

    # 7. Вывод результатов
    if output.write_duplicates_to_csv(duplicates, args.output):
        logging.info(f"Поиск завершён. Результаты сохранены в '{args.output}'.")
    else:
        logging.error("Ошибка при записи результатов в файл CSV.")


if __name__ == "__main__":
    main()
