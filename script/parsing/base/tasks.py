from parsing.base.base_sql import ConnectSqlite
from peewee import IntegerField, TextField, BooleanField, Model


class Tasks(Model):
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
        table_name = 'tasks'
        database = ConnectSqlite.get_connect()

    def __str__(self):
        return f'{self.date} {self.id_from_city} {self.id_to_city} {self.info}'
