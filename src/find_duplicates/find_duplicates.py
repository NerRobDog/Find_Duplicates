from tqdm import tqdm
from modules import scanner, grouper, comparer, output, logger, utils, hasher
import logging, os

logging.root = logger.logger.logger


def main():
    """
    Главный скрипт для поиска дубликатов файлов.
    Этапы обработки:
      1. Сканирование директорий (получение полного списка файлов).
      2. Группировка файлов по размеру.
      3. Фильтрация каждой группы по partial-содержимому.
      4. Группировка по хэшу (если включено) или по весу (если отключено) для отфильтрованных кандидатов.
      5. Побайтовое сравнение для окончательной верификации (если включено).
      6. Вывод результатов в CSV.
    """
    # 1. Парсинг аргументов и настройка логгера
    args = utils.parse_arguments()
    logger.setup_logger(args.log_level)
    logging.debug(f"Аргументы: {args}")
    logging.info("Скрипт запущен.")

    # 2. Сканирование директорий
    all_files = []
    for directory in tqdm(args.directory, desc="Сканирование директорий", unit=" дир"):
        try:
            if not utils.validate_directory(directory):
                logging.error(f"Директория '{directory}' не найдена или недоступна.")
                continue
        except Exception as e:
            logging.error(f"Ошибка при проверке директории '{directory}': {e}")
            continue
        files = scanner.scan_directory(
            directory=directory,
            include_hidden=args.include_hidden,
            skip_inaccessible=args.skip_inaccessible,
            exclude=args.exclude
            # pbar можно передать, если нужен общий progress bar
        )
        all_files.extend(files)
    if not all_files:
        logging.info("Файлы не найдены в указанных директориях.")
        output.write_duplicates_to_csv({}, args.output)
        return

    # 3. Группировка по размеру
    size_groups = grouper.group_files_by_size(all_files)
    if not size_groups:
        logging.info("Нет групп файлов с одинаковым размером — дубликаты не обнаружены.")
        output.write_duplicates_to_csv({}, args.output)
        return
    logging.info(f"Найдено {len(size_groups)} групп по размеру.")

    # 4. Фильтрация по partial-содержимому для всех групп.
    # Для каждой группы по размеру вычисляем partial-содержимое (например, первые и последние 1КБ).
    # Оставляем только те группы, где 2 и более файла имеют одинаковое partial-содержимое.
    partial_candidates = {}  # ключ: (size, partial_key), значение: список файлов
    for size, file_group in tqdm(size_groups.items(), desc="Partial фильтрация", unit=" группа "):
        if len(file_group) < 2:
            continue
        partial_dict = {}
        for file in file_group:
            try:
                key = hasher.get_partial_content(file)
                partial_dict.setdefault(key, []).append(file)
            except Exception as e:
                logging.error(f"Ошибка при получении partial content для {file}: {e}")
                continue
        for key, group in partial_dict.items():
            if len(group) >= 2:
                partial_candidates[(size, key)] = group
    if not partial_candidates:
        logging.info("Нет кандидатов после partial фильтрации.")
        output.write_duplicates_to_csv({}, args.output)
        return
    logging.info(f"Найдено {len(partial_candidates)} групп после partial фильтрации.")

    # 5. Группировка по хэшу или по весу (если хэш отключён) для каждого partial-кандидата.
    hash_candidates = {}
    for (size, p_key), group in tqdm(partial_candidates.items(), desc="Группировка по хэшу", unit=" групп "):
        if not args.disable_hash_check:
            # Если хэширование включено, группируем по хэшу
            if args.parallel:
                from modules.hasher import compute_hash_parallel
                workers = args.workers or os.cpu_count()
                hash_results = compute_hash_parallel(group, args.hash_type, num_workers=workers)
                group_by = {}
                for file, h in hash_results.items():
                    if h:
                        group_by.setdefault(h, []).append(file)
            else:
                group_by = comparer.group_by_hash(group, args.hash_type)
        else:
            # Если хэширование отключено, используем вес (размер) как ключ
            group_by = {size: group}

        for key, g in group_by.items():
            if len(g) >= 2:
                # Объединяем группы, если несколько partial-групп дают один и тот же ключ
                hash_candidates.setdefault(key, []).extend(g)
    if not hash_candidates:
        logging.info("Нет кандидатов после группировки по хэшу/весу.")
        output.write_duplicates_to_csv({}, args.output)
        return
    # Если используется хэширование, логируем по числу групп по хэшу, иначе по числу групп по весу.
    if not args.disable_hash_check:
        logging.info(f"Найдено {len(hash_candidates)} групп после хэширования.")
    else:
        logging.info(f"Найдено {len(hash_candidates)} групп после фильтрации по весу.")

    # 6. Побайтовое сравнение для окончательной верификации (если включено)
    final_duplicates = {}
    for key, group in tqdm(hash_candidates.items(), desc="Побайтовая проверка", unit=" группа"):
        if not args.disable_byte_compare:
            logging.info(f"Проверка по байтам для группы {key}:")
            verified = comparer.verify_by_byte(group)
            if verified and len(verified) >= 2:
                final_duplicates[key] = verified
        else:
            final_duplicates[key] = [utils.get_file_info(f) for f in group]
    if not final_duplicates:
        logging.info("Дубликаты не обнаружены после побайтовой проверки.")
        output.write_duplicates_to_csv({}, args.output)
        return

    # 7. Вывод результатов в CSV
    if output.write_duplicates_to_csv(final_duplicates, args.output):
        logging.info(f"Поиск завершён. Результаты сохранены в '{args.output}'.")
    else:
        logging.error("Ошибка при записи результатов в файл CSV.")


if __name__ == "__main__":
    main()