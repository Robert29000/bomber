import logging
from logging.handlers import RotatingFileHandler

FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")


def get_file_handler():
    file_handler = RotatingFileHandler('bot.log', maxBytes=102400)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    if not len(logger.handlers):
        logger.addHandler(get_file_handler())
    logger.propagate = False
    return logger
