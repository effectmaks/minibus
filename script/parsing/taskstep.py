from parsing.log import logger
import datetime

from parsing.base.task import Task
from parsing.base.settings import Settings
from parsing.base.usertask import Usertask

from parsing.citieshtml import DownloadCities
from typing import List, Dict
from parsing.dates import Dates
from parsing.routeshtml import DownloadRoutes
from parsing.exception import ExceptionMsg
from parsing.interface import Interface


class TaskItem:
    def __init__(self):
        self.id_base: int
        self.id_chat: str
        self.info: str

    @property
    def info_list(self):
        return f'{self.id_chat}: {self.info}'


class StepsTasks:
    def __init__(self):
        self._dict_task_active: Dict[str, TaskItem] = dict()

    def s1_view_active_task(self, interface: Interface):
        """
        Показать все активные задачи проверки рейса
        """
        logger.info(f'{interface.id_chat} Шаг 1 s1_view_active "{interface.msg_user}"')
        self._set_msg_list_tasks_from_base(interface)

    def _set_msg_list_tasks_from_base(self, interface: Interface):
        """
        Список заданий для пользователя
        """
        try:
            usertasks = Usertask.select(Usertask, Task).join(Task) \
                .where(Usertask.id_chat == interface.id_chat) \
                .order_by(Task.date, Task.info) \
                .execute()
            count = len(usertasks)
            for usertask, id_chat in zip(usertasks, range(1, count + 1)):
                user_task = self.create_info_task(id_chat, usertask.id, usertask.task.date,
                                             usertask.task.id_from_city, usertask.task.id_to_city,
                                             usertask.task.info)
                self._dict_task_active[str(id_chat)] = user_task
            self.create_msg_list_task(interface)
        except Exception as e:
            raise Exception(f'Ошибка: Выгрузка списка заданий! {str(e)}')

    def s2_delete_task(self, interface: Interface):
        """
        По выбранному номеру удаляет задание
        :return:
        """
        logger.info(f'{interface.id_chat} Шаг 2 s2_delete_task "{interface.msg_user}"')
        task_delete = self._dict_task_active.get(interface.msg_user)
        if not task_delete:
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        StepsTasks.delete_task(task_delete.id_base)
        self._dict_task_active.pop(interface.msg_user)
        interface.msg_info.text = f'Слежение №{task_delete.id_chat} удалено!'
        self.create_msg_list_task(interface)

    def create_msg_list_task(self, interface: Interface):
        """
        Сообщение для пользователя со списком заданий
        """
        datetime_last_check = TimeTask.get_str()
        if len(self._dict_task_active) == 0:
            interface.b_end = True
            interface.list_task = 'Нет активных заданий!'
            return
        s_out = "\n────────────────\n".join([task.info_list for task in self._dict_task_active.values()])
        interface.list_task = f'Ваши слежения рейсов:\n─────────────👀──\n{s_out}' \
                              f'\n───────────🚗──🚙─\n' \
                              f'✅ Последняя проверка\nрейсов была в {datetime_last_check}' \
                              f'\n──────────────👀──\n' \
                              f'Введите номер слежения\nдля его удаления:'

    def get_id_base(self, id):
        return self._dict_task_active.get(id)

    def create_info_task(self, id_chat, id_base, date, id_city_from, id_city_to, info):
        """
        Заполнить информацию о заданиях
        :return:
        """
        task = TaskItem()
        dw_ct = DownloadCities()
        city_from = dw_ct.cities(id_city_from)
        city_to = dw_ct.cities(id_city_to)
        task.info = f'{Dates().get_short_info(date)} {info}\n     {city_from} - {city_to}'
        task.id_base = id_base
        task.id_chat = id_chat
        return task

    @classmethod
    def get_tasks_have_place(cls):
        """
        Выгрузка заданий с рейсами со свободными местами
        :return:
        """
        try:
            logger.debug(f'Выгрузка заданий c рейсами со свободными местами')
            return Usertask.select()\
                            .join(Task) \
                            .where(Task.have_place==True) \
                            .order_by(Task.date).execute()
        except Exception as e:
            raise Exception(f'Ошибка выгрузки c базы. {str(e)}')

    @classmethod
    def get_msg_delete(cls, id_look):
        """
        ID сообщения которое надо удалить
        :return:
        """
        try:
            logger.debug(f'Выгрузка ID сообщения которое надо удалить')
            usertasks = Usertask.select(Usertask.id_msg_delete).join(Task) \
                .where(Usertask.id == id_look).execute()
            for usertask in usertasks:
                return usertask.id_msg_delete
        except Exception as e:
            raise Exception(f'Ошибка выгрузки c базы Usertask. {str(e)}')

    @classmethod
    def update_task_msg_delete(cls, id_base, id_delete, task_off):
        """
        Обновить ID отправленного сообщения
        """
        try:
            Usertask.update({Usertask.id_msg_delete: id_delete, Usertask.task_off: task_off}) \
                .where(Usertask.id == id_base).execute()
        except Exception as e:
            raise Exception(f'Ошибка обновить id_base {id_base}, id_msg {id_delete} в Usertask {str(e)}')

    @classmethod
    def delete_task(cls, id_base):
        """
        Удалить задание с ID
        """
        try:
            Usertask.delete().where(Usertask.id == id_base).execute()
        except Exception as e:
            logger.error(f'Ошибка удалить id_base {id_base} в Usertask {str(e)}')
            raise ExceptionMsg(f'Ошибка: Слежение не удалено.\nПовторите ввод числа.')

    @classmethod
    def _get_id_task_mirror(cls, date, id_city_from, id_city_to, info, time_from):
        """
        Вернуть id похожего слежения
        :return:
        """
        tasks = None
        try:
            logger.debug(f'Выгрузка ID похожего задания')
            tasks = Task.select() \
                .where(Task.date == date,
                       Task.id_from_city == id_city_from,
                       Task.id_to_city == id_city_to,
                       Task.info == info,
                       Task.time_from == time_from).execute()
        except Exception as e:
            raise Exception(f'Ошибка выгрузки Task c базы. {str(e)}')
        for task in tasks:
            return task

    @classmethod
    def _get_id_task(cls, date, id_city_from, id_city_to, info, time_from):
        """
        Вернуть id похожего слежения, или создать новое
        :return:
        """
        try:
            logger.debug(f'Проверка что задание есть в базе')
            task = cls._get_id_task_mirror(date, id_city_from, id_city_to, info, time_from)
            if task:
                return task
            task = Task.create(date=date,
                               id_from_city=id_city_from,
                               id_to_city=id_city_to,
                               info=info,
                               time_from=time_from).save()
            task = cls._get_id_task_mirror(date, id_city_from, id_city_to, info, time_from)
            if task:
                return task
            else:
                raise Exception("Ошибка: Запись с заданием в базу не добавилась!")
        except Exception as e:
            raise Exception(f'Ошибка создания записи. {str(e)}')

    @classmethod
    def add_task_user(cls, id_chat, date, id_city_from, id_city_to, info, time_from):
        """
        Добавить слежение пользователю
        :return:
        """
        try:
            logger.debug(f'Добавить слежение пользователю')
            task = cls._get_id_task(date, id_city_from, id_city_to, info, time_from)
            Usertask.create(id_chat=id_chat, task=task).save()
        except Exception as e:
            raise Exception(f'Ошибка создания записи Usertask. {str(e)}')


class RunTask:
    @classmethod
    def check(cls):
        """
        Просмотр рейсов в базе.(заданий)
        Выгружает в дни с сервера.
        Просматривает дни по наличию времени
        :return:
        """
        logger.info('CELERY Проверка может появились новые места')
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
                            if task.info == route.info_short and not task.have_place and route.have_place:
                                logger.info(f"CELERY ОСВОБОДИЛОСЬ место {task.date} {task.info} "
                                             f"from {task.id_from_city} to {task.id_to_city}")
                                cls._update_task_have_place(date, task.id_from_city, task.id_to_city, task.info, True)
                            elif task.info == route.info_short and task.have_place and not route.have_place:
                                logger.info(f"CELERY СНОВО ЗАНЯТО место {task.date} {task.info} "
                                             f"from {task.id_from_city} to {task.id_to_city}")
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
            logger.debug(f'Выгрузка заданий c базы на {date}')
            return Task.select(Task.date, Task.id_from_city, Task.id_to_city, Task.info, Task.have_place).distinct() \
                .where(Task.date == date).order_by(Task.date, Task.id_from_city).execute()
        except Exception as e:
            raise Exception(f'Ошибка выгрузки c базы. {str(e)}')

    @classmethod
    def _get_routes_server(cls, date, city_from, city_to):
        """
        Выгрузка заданий с рейсами которые надо проверить
        :return:
        """
        try:
            logger.info(f'CELERY Выгрузка рейсов с сервера на {date}, {city_from}, {city_to}')
            down_routes = DownloadRoutes(date, city_from, city_to)
            routes = down_routes.list
            if routes:
                return routes
            logger.debug(f'Ошибка нет рейсов на {date}, {city_from}, {city_to}')
        except ExceptionMsg as e:
            logger.warning(str(e))
        except Exception as e:
            raise Exception(f'Ошибка выгрузки с сервера. {str(e)}')

    @classmethod
    def _update_task_have_place(cls, date, city_from, city_to, info, have_place):
        """
        Обновление рейсов в базе в которых есть места
        """
        try:
            date_time_str = Dates.create_date_time_str(datetime.datetime.now())
            if have_place:
                update_data = {Task.have_place: True, Task.time_on: date_time_str, Task.time_off: "", }
            else:
                update_data = {Task.have_place: False, Task.time_off: date_time_str, }
            Task.update(update_data) \
                .where(Task.date == date, Task.id_from_city == city_from,
                       Task.id_to_city == city_to, Task.info == info) \
                .execute()
        except Exception as e:
            raise Exception(f'Ошибка обновления на рейс {date}, {city_from}, {city_to}. {str(e)}')


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
            raise Exception(f'Ошибка обновления поля {cls.NAME_DATETIME_TASK_CHECK}: {datetime_check} {str(e)}')

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
            raise Exception(f'Ошибка выгрузки поля {cls.NAME_DATETIME_TASK_CHECK} {str(e)}')

    @classmethod
    def add_name(cls, name):
        """
        Вернуть значение даты последней проверки рейсов
        :return: Дата в текстовом формате
        """
        try:
            Settings.create(name=datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S.%f'), value=name).save()
        except Exception as e:
            raise Exception(f'Ошибка добавления имени в базу {cls.NAME_USER} {name} {str(e)}')


if __name__ == '__main__':
    #RunTask.check()  # Проверка может появились новые места
    RunTask._update_task_have_place("08.03.2023", 5, 23, "(12:15-14:35)", True)
