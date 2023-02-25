from parsing.base.base_sql import ConnectSqlite
from peewee import IntegerField, TextField, BooleanField, Model

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


if __name__ == '__main__':
    print(Cities.select().execute())
