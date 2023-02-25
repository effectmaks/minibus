from peewee import IntegerField, TextField, BooleanField, Model
from peewee import SqliteDatabase
import platform



class ExceptionBase(Exception):
    def __init__(self, err_message: str = ''):
        logging.error(err_message)
        super().__init__(err_message)


class ExceptionInsert(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка создания записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ExceptionSelect(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка чтения записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ExceptionDelete(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка удаления записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


class ExceptionUpdate(Exception):
    def __init__(self, name_table: str = '', err_script_message: str = ''):
        err_message = f'Ошибка обновления записи в таблице {name_table}'
        logging.error(err_message)
        logging.error(err_script_message)
        super().__init__(err_message)


BASE_PATH = '../db.sqlite3'
if platform.system().startswith('L'):
    BASE_PATH = 'db.sqlite3'
print(BASE_PATH)

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


class Cities(Model):
    """
    База данных таблица городов
    """
    id = IntegerField()
    name = TextField()
    sort = IntegerField()

    class Meta:
        table_name = 'cities'
        database = ConnectSqlite.get_connect()


class Look(Model):
    """
    База данных таблица городов
    """
    id = IntegerField()
    id_chat = IntegerField()
    date = TextField()
    id_from_city = IntegerField()
    id_to_city = IntegerField()
    info = TextField()
    have_place = BooleanField()
    id_msg_delete = IntegerField()

    class Meta:
        table_name = 'look'
        database = ConnectSqlite.get_connect()

    def __str__(self):
        return f'{self.date} {self.id_from_city} {self.id_to_city} {self.info}'


class Settings(Model):
    """
    База данных таблица настроек и данных
    """
    id = IntegerField()
    name = TextField()
    value = TextField()

    class Meta:
        table_name = 'settings'
        database = ConnectSqlite.get_connect()

if __name__ == '__main__':
   print(Cities.select().execute())
