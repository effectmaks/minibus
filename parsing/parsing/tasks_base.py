import datetime

from parsing.base_sql import Look,Settings
from parsing.cities import DownloadCities
from typing import List, Dict
from parsing.message import MsgAnswer, MsgControl
from parsing.dates import Dates
from parsing.routes import DownloadRoutes


class Task:
    def __init__(self):
        self.id_base: int
        self.id_chat: str
        self.info: str

    @property
    def info_list(self):
        return f'{self.id_chat}: {self.info}'


class StepsTasks(MsgControl):
    def __init__(self):
        super().__init__()
        self._dict_task_active: Dict[str, Task] = dict()

    def s1_view_active(self, id_chat):
        """
        Показать все активные задачи проверки рейса
        :param id_chat:
        :return:
        """
        try:
            tasks = Look.select().where(Look.id_chat == id_chat).order_by(Look.date, Look.info).execute()
            count = len(tasks)
            for task_item, id_chat in zip(tasks, range(1, count + 1)):
                task = self.create_info_task(id_chat, task_item.id, task_item.date,
                                task_item.id_from_city, task_item.id_to_city,
                                task_item.info)
                self._dict_task_active[str(id_chat)] = task
            datetime_last_check = TimeTask.get_str()
        except Exception as e:
            print(str(e))
            raise Exception('Ошибка: Выгрузка списка заданий!')
        if len(self._dict_task_active) == 0:
            self.b_end = True
            return MsgAnswer('', 'Нет активных заданий!')
        return MsgAnswer('', 'Ваши слежения рейсов:\n─────────────👀──\n' +
                             '\n────────────────\n'
                             .join([task.info_list for task in self._dict_task_active.values()]) +
                             '\n───────────🚗──🚙─\n' +
                             f'✅ Последняя проверка\nрейсов была в {datetime_last_check}'
                             f'\n──────────────👀──\n'
                             f'Введите номер слежения\nдля его удаления:')

    def s2_delete_task(self, id_chat, id_list_text):
        """
        По выбранному номеру удаляет задание
        :return:
        """
        task_delete = self._dict_task_active.get(id_list_text)
        if not task_delete:
            raise Exception('Ошибка: Введите число из списка!')
        StepsTasks.delete_task(task_delete.id_base)
        self.b_end = True
        return MsgAnswer('', f'Слежение №{task_delete.id_chat} удалено!')


    def get_id_base(self, id):
        return self._dict_task_active.get(id)

    def create_info_task(self, id_chat, id_base, date, id_city_from, id_city_to, info):
        """
        Заполнить информацию о заданиях
        :return:
        """
        task = Task()
        dw_ct = DownloadCities()
        city_from = dw_ct.cities(id_city_from)
        city_to = dw_ct.cities(id_city_to)
        task.info = f'{date} {info}\n     {city_from} - {city_to}'
        task.id_base = id_base
        task.id_chat = id_chat
        return task

    def get_tasks_have_place(cls):
        """
        Выгрузка заданий с рейсами со свободными местами
        :return:
        """
        try:
            print(f'Выгрузка заданий c рейсами со свободными местами')
            return Look.select(Look.id, Look.id_chat, Look.date, Look.id_from_city,
                               Look.id_to_city, Look.info, Look.id_msg_delete) \
                .where(Look.have_place == True).order_by(Look.date).execute()
        except Exception as e:
            print(f'Ошибка выгрузки c базы. {str(e)}')

    @classmethod
    def get_msg_delete(cls, id_chat, id_look):
        """
        ID сообщения которое надо удалить
        :return:
        """
        try:
            print(f'Выгрузка ID сообщения которое надо удалить')
            looks = Look.select(Look.id_msg_delete) \
                .where(Look.id_chat == id_chat, Look.id == id_look).execute()
            for l in looks:
                return l.id_msg_delete
        except Exception as e:
            print(f'Ошибка выгрузки c базы. {str(e)}')

    @classmethod
    def update_task_msg_delete(cls, id_base, id_delete):
        """
        Обновить ID отправленного сообщения
        """
        try:
            Look.update({Look.id_msg_delete: id_delete}) \
                .where(Look.id == id_base).execute()
        except Exception as e:
            print(f'Ошибка обновить id_base {id_base}, id_msg {id_delete} {str(e)}')

    @classmethod
    def delete_task(cls, id_base):
        """
        Удалить задание с ID
        """
        try:
            Look.delete().where(Look.id == id_base).execute()
        except Exception as e:
            print(f'Ошибка удалить id_base {id_base} {str(e)}')
            raise Exception(f'Ошибка: Слежение не удалено.\nПовторите ввод числа.')

    @classmethod
    def check_task_mirror(cls, id_chat, date, id_city_from, id_city_to, info):
        """
        Проверка что пользователь выбрал, такое же задания на слежения
        :return:
        """
        look = None
        try:
            print(f'Задание на слежение с базы которое выбрал пользователь')
            look = Look.select(Look.id) \
                .where(Look.id_chat == id_chat,
                       Look.date == date,
                       Look.id_from_city == id_city_from,
                       Look.id_to_city == id_city_to,
                       Look.info == info).execute()
        except Exception as e:
            print(f'Ошибка выгрузки c базы. {str(e)}')
        for _ in look:
            raise Exception('Ошибка: Это рейс вы уже отслеживаете!\nВведите другой номер рейса.')


class RunTask:
    @classmethod
    def check(cls):
        """
        Просмотр рейсов в базе.(заданий)
        Выгружает в дни с сервера.
        Просматривает дни по наличию времени
        :return:
        """

        for date in cls._get_dates():
            id_from, id_to = 0, 0
            tasks = cls._get_tasks(date)
            if tasks:
                routes = None
                for task in tasks:
                    if id_from and id_to:
                        if id_from != task.id_from_city or id_to != task.id_to_city:
                            routes = cls._get_routes_server(task.date, task.id_from_city, task.id_to_city)
                            id_from = task.id_from_city
                            id_to = task.id_to_city
                    else:
                        routes = cls._get_routes_server(task.date, task.id_from_city, task.id_to_city)
                        id_from = task.id_from_city
                        id_to = task.id_to_city
                    if routes:
                        for route in routes:
                            if task.info == route.info_short and route.have_place:
                                cls._update_task_have_place(date, task.id_from_city, task.id_to_city, task.info, True)
                            elif task.info == route.info_short and task.have_place and not route.have_place:
                                cls._update_task_have_place(date, task.id_from_city, task.id_to_city, task.info, False)
        TimeTask.set(datetime.datetime.now())

    @classmethod
    def _get_dates(cls):
        """
        Даты на которые можно посмотреть рейсы
        :return:
        """
        dates = Dates()
        dates.have_list()
        return dates.items

    @classmethod
    def _get_tasks(cls, date):
        """
        Выгрузка заданий с рейсами которые надо проверить, за 7 дней
        :return:
        """
        try:
            print(f'Выгрузка заданий c базы на {date}')
            return Look.select(Look.date, Look.id_from_city, Look.id_to_city, Look.info, Look.have_place).distinct() \
                .where(Look.date == date).order_by(Look.date, Look.id_from_city).execute()
        except Exception as e:
            print(f'Ошибка выгрузки c базы. {str(e)}')

    @classmethod
    def _get_routes_server(cls, date, city_from, city_to):
        """
        Выгрузка заданий с рейсами которые надо проверить
        :return:
        """
        try:
            print(f'Выгрузка рейсов с сервера на {date}, {city_from}, {city_to}')
            down_routes = DownloadRoutes(date, city_from, city_to)
            routes = down_routes.list
            if routes:
                return routes
            print(f'Ошибка нет рейсов на {date}, {city_from}, {city_to}')
        except Exception as e:
            print(f'Ошибка выгрузки с серера. {str(e)}')

    @classmethod
    def _update_task_have_place(cls, date, city_from, city_to, info, have_place):
        """
        Обновление рейсов в базе в которых есть места
        """
        try:
            Look.update({Look.have_place: have_place}) \
                .where(Look.date == date, Look.id_from_city == city_from,
                       Look.id_to_city == city_to, Look.info == info) \
                .execute()
        except Exception as e:
            print(f'Ошибка обновления на рейс {date}, {city_from}, {city_to}. {str(e)}')


class TimeTask:
    """
    Отображение времени последней проверки
    """
    NAME_DATETIME_TASK_CHECK = "DATETIME_TASK_CHECK"  # имя поля даты последней проверки рейсов
    NAME_USER = "USER"  # имя
    MSK_DATETIME_VIEW = "%d.%m.%Y %H:%M:%S"

    @classmethod
    def set(cls, datetime_check):
        """
        Обновление поля даты последней проверки рейсов
        :param datetime_check: Время класса datetime
        """
        try:
            datetime_str = datetime_check.strftime(cls.MSK_DATETIME_VIEW)
            Settings.update({Settings.value: datetime_str}) \
                    .where(Settings.name == cls.NAME_DATETIME_TASK_CHECK) \
                    .execute()
        except Exception as e:
            print(f'Ошибка обновления поля {cls.NAME_DATETIME_TASK_CHECK}: {datetime_check} {str(e)}')

    @classmethod
    def get_str(cls):
        """
        Вернуть значение даты последней проверки рейсов
        :return: Дата в текстовом формате
        """
        try:
            setting = Settings.select(Settings.value) \
                              .where(Settings.name == cls.NAME_DATETIME_TASK_CHECK) \
                              .execute()
            for s in setting:
                return s.value[-8:]
        except Exception as e:
            print(f'Ошибка выгрузки поля {cls.NAME_DATETIME_TASK_CHECK} {str(e)}')

    @classmethod
    def add_name(cls, name):
        """
        Вернуть значение даты последней проверки рейсов
        :return: Дата в текстовом формате
        """
        try:
            Settings.create(name=datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S.%f'), value=name).save()
        except Exception as e:
            print(f'Ошибка добавления имени в базу {cls.NAME_USER} {name} {str(e)}')


if __name__ == '__main__':
    print(TimeTask.add_name(8523))  # запуск каждые 5 мин проверка заданий
    # DownloadCities().download_cities_from()  # один раз в день обновлять id городов
    # раз в день удалять старые задания
