from parsing.base.base_sql import ConnectSqlite
from peewee import IntegerField, TextField, BooleanField, TimeField, DateTimeField, Model


class Task(Model):
    """
    База данных таблица городов
    """
    id = IntegerField()
    date = TextField()
    id_from_city = IntegerField()
    id_to_city = IntegerField()
    info = TextField()
    have_place = BooleanField()
    time_from = TimeField()
    time_on = DateTimeField()
    time_off = DateTimeField()

    class Meta:
        table_name = 'task'
        database = ConnectSqlite.get_connect()

    def __str__(self):
        return f'{self.date} {self.id_from_city} {self.id_to_city} {self.info}'
