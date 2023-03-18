import os
import platform
import logging
from logging.handlers import TimedRotatingFileHandler


FILE_PATH = '../logs/py_log_debug.log'
level = logging.DEBUG
if platform.system().startswith('L'):
    FILE_PATH = 'logs/py_log.log'  # если запускать с Linux python3 start.py
    level = logging.INFO

# Проверяем наличие файла по пути FILE_PATH и создаем его при отсутствии
if not os.path.exists(FILE_PATH):
    open(FILE_PATH, 'a').close()

log_format = "%(asctime)s-%(levelname)s: %(message)s"
stream_handler = logging.StreamHandler()
stream_handler.setLevel(level)

file_handler = TimedRotatingFileHandler(FILE_PATH, when='midnight', backupCount=10)
file_handler.setFormatter(logging.Formatter(log_format))
logging.basicConfig(level=level, format=log_format,
                    handlers=[file_handler,
                              stream_handler]
                    )

logger = logging.getLogger(FILE_PATH)