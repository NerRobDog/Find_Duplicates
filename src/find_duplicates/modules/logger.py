import logging
from typing import Optional, Callable
from functools import wraps


class LoggerWrapper:
    def __init__(self, name: str = "FindDuplicatesLogger", log_level: str = "INFO", log_file: Optional[str] = None):
        # Создаём объект стандартного логгера
        self.logger = logging.getLogger(name)
        # Устанавливаем уровень
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

        # Обработчик для вывода в консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Дополнительно, при необходимости, пишем в файл
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def critical(self, message: str):
        self.logger.critical(message)

    def set_level(self, level: str):
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))


# Создаём глобальный объект логгера с настройками по умолчанию
logger = LoggerWrapper(log_level="INFO")


def setup_logger(level: str = "INFO", log_file: Optional[str] = None):
    """
    Утилита для перенастройки глобального логгера на нужный уровень и/или файл.
    """
    logger.set_level(level)
    # Если нужен вывод в файл — можно пересоздать логгера, но тогда придётся аккуратно
    # обрабатывать существующие хэндлеры. Для простоты логика может быть дополнена.
    # Либо сделать вариант с logger = LoggerWrapper(name, level, log_file).
    # Ниже — упрощённый пример, просто меняем уровень:
    if log_file:
        # Если хотим добавить file_handler:
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger.logger.addHandler(file_handler)


def log_execution(level: str = "INFO", message: Optional[str] = None):
    """
    Декоратор для автоматического логирования выполнения функций.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            log_msg = message or f"Выполнение функции: {func.__name__}"
            getattr(logger, level.lower(), logger.info)(f"🚀 Начало: {log_msg}")
            try:
                result = func(*args, **kwargs)
                getattr(logger, level.lower(), logger.info)(f"✅ Завершение: {log_msg}")
                return result
            except Exception as e:
                logger.error(f"❌ Ошибка в функции {func.__name__}: {e}")
                raise

        return wrapper

    return decorator
