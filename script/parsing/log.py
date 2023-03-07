import platform
import logging


FILE_PATH = '../logs/py_log_debug.log'
level = logging.DEBUG
if platform.system().startswith('L'):
    FILE_PATH = 'logs/py_log.log'  # если запускать с Linux python3 start.py
    level = logging.INFO

log_format = "%(asctime)s-%(levelname)s: %(message)s"
stream_handler = logging.StreamHandler()
stream_handler.setLevel(level)
logging.basicConfig(level=level, format=log_format,
                    handlers=[logging.FileHandler(FILE_PATH, mode='a'),
                              stream_handler]
                    )

logger = logging.getLogger(FILE_PATH)

logger.info(f"Testing logger {FILE_PATH}...")
"""


FILE_PATH = '../logs/py_log_debug'
level = logging.DEBUG
if platform.system().startswith('L'):
    FILE_PATH = 'logs/py_log'  # если запускать с Linux python3 start.py
    level = logging.INFO

log_format = "%(asctime)s-%(levelname)s: %(message)s"
logger = logging.getLogger(FILE_PATH)
logger.setLevel(level)

# настройка обработчика и форматировщика для logger2
handler_file = logging.FileHandler(f"{FILE_PATH}.log", mode='a')
formatter = logging.Formatter(log_format)

# добавление форматировщика к обработчику
handler_file.setFormatter(formatter)
# добавление обработчика к логгеру
logger.addHandler(handler_file)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

logging.basicConfig(level=level, format=log_format,
                    handlers=[handler_file,
                              stream_handler],

                    )

logger.info(f"Testing logger {FILE_PATH}...")
"""