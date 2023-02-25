from parsing.base.base_sql import ConnectSqlite
from peewee import IntegerField, TextField, BooleanField, Model


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
