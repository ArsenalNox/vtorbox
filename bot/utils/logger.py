import traceback

from loguru import logger


def debug_only(record):
    """Функция для фильтрации записи в логи только для уровня DEBUG"""
    return record["level"].name == 'DEBUG'


def warning_only(record):
    """Функция для фильтрации записи в логи только для уровня WARNING"""
    return record["level"].name == 'WARNING'


def debug_log_write():
    logger.add('debug.log', format="{time} {level} {message}", level="DEBUG", rotation="5 MB",
               compression="zip", filter=debug_only)


def warning_log_write():
    logger.add('warning.log', format="{time} {level} {message}", level="WARNING", rotation="5 MB",
               compression="zip", filter=warning_only)


