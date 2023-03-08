from parsing.base.base_sql import ConnectSqlite
from peewee import IntegerField, TextField, BooleanField, TimeField, Model
from peewee import ForeignKeyField
from parsing.base.task import Task


class Usertask(Model):
    """
    База данных таблица городов
    """
    id = IntegerField()
    id_chat = IntegerField()
    task = ForeignKeyField(Task, db_column='task', related_name='usertask')
    id_msg_delete = IntegerField()

    class Meta:
        table_name = 'usertask'
        database = ConnectSqlite.get_connect()
