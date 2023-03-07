from parsing.log import logger
from peewee import SqliteDatabase
import platform


BASE_PATH = '../db.sqlite3'
if platform.system().startswith('L'):
    BASE_PATH = 'db.sqlite3'
logger.debug(f'Путь к базе {BASE_PATH}')


class ConnectSqlite:
    """
    Класс Singleton выдает один и тот же объект
    """
    __connect = None

    @classmethod
    def get_connect(cls):
        if not cls.__connect:
            try:
                cls.__connect = SqliteDatabase(BASE_PATH)
            except Exception as err:
                raise ExceptionBase(f'Ошибка подключения БД: {str(err)}')
        return cls.__connect
