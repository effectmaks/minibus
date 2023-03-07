from parsing.log import logger

from parsing.routeshtml import DownloadRoutes, Route
from parsing.citieshtml import DownloadCities
from parsing.dates import Dates
from parsing.exception import ExceptionMsg
from parsing.base.task import Task
from parsing.taskstep import StepsTasks
from parsing.interface import Interface


class StepsFind:
    def __init__(self):
        self._dates = Dates()
        self._date_choose: str
        self._serv_cities: DownloadCities
        self._id_city_from: str
        self._id_city_to: str
        self._down_routes: DownloadRoutes

    def s1_date_print(self, interface: Interface):
        """
        Список дат для поиска
        :return:
        """
        logger.debug("Шаг 1 StepsFind")
        interface.list_msg = f'Даты рейсов маршрутки:\n──────────────👀──\n' \
                             f'{self._dates.have_list()}\n──────👀──────────\n' \
                             f'Введите дату (например: "18"):'

    def s2_date_check(self, interface: Interface):
        """
        Проверка выбранной даты
        :param id:
        """
        self._date_choose = self._dates.get_day_dict(interface.msg_user)
        if not self._date_choose:
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        self._serv_cities = DownloadCities()
        interface.msg_do = self._s2_get_date_str()
        interface.list_msg = f'Список остановок выезда:\n─────👀───────────\n' \
                             f'{self._serv_cities.cities()}\n────────👀────────\n' \
                             f'Укажите пункт выезда (введите число):'

    def _s2_get_date_str(self):
        return f'Дата: {self._dates.get_short_info(self._date_choose)}'

    def s3_city_from_print(self, interface: Interface):
        """
        Вопрос пункт выезда по ID пользователя
        :param id:
        :return:
        """
        if not self._serv_cities.cities(interface.msg_user):
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        s_out = self._serv_cities.download_cities_to(interface.msg_user)
        if not s_out:
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        self._id_city_from = interface.msg_user
        interface.msg_do = self._s2_get_date_str() + "\n" + self._s3_get_from_city()
        interface.list_msg = f'Список остановок приезда:\n─────👀───────────\n{s_out}' \
                             f'\n────────────👀────\nВведите конечный пункт\n(введите число):'

    def _s3_get_from_city(self):
        city_choose = self._serv_cities.cities(self._id_city_from)
        return f'Из пункта: {city_choose}'

    def s4_city_to_print(self, interface: Interface):
        self._s4_city_to_check(interface)
        self._s4_sity_download(interface)
        self._s4_city_to_print(interface)

    def _s4_city_to_check(self, interface: Interface):
        if interface.msg_user == self._id_city_from:
            raise ExceptionMsg('Ошибка: Не должны повторяться города!')
        if not self._serv_cities.cities(interface.msg_user):
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        self._id_city_to = interface.msg_user
        interface.msg_do = self._s2_get_date_str() + "\n" + self._s3_get_from_city() + "\n" + self._s4_get_to_city()

    def _s4_get_to_city(self):
        city_choose = self._serv_cities.cities(self._id_city_to)
        if not city_choose:
            raise ExceptionMsg('Ошибка: Введите число!')
        return f'В пункт: {city_choose}'

    def _s4_sity_download(self, interface: Interface):
        """
        Скачать рейсы с сайта
        """
        try:
            self._down_routes = DownloadRoutes(self._date_choose, self._id_city_from, self._id_city_to,
                                               id_chat=interface.id_chat)
        except ExceptionMsg as e:
            interface.b_end = True
            raise ExceptionMsg(f'Ошибка: {str(e)}.')

    def _s4_city_to_print(self, interface: Interface):
        """
        Сформировать сообщение с рейсами
        """
        routes = self._down_routes.list
        if not routes:
            raise ExceptionMsg('Ошибка: Нет данных!')
        s_out = '\n────────👀────────\nВыберите номер рейса для слежения: \n' \
                '🔴 - мест нет, можно отслеживать\n' \
                '🟡 - уже отслеживаете\n' \
                '🟢 - свободные билеты есть'
        s_out = f"Список рейсов на {self._dates.get_short_info(self._date_choose)}:\n─👀──────────────\n" + \
                '\n'.join([r.info for r in routes]) + s_out
        interface.list_msg = s_out

    def s5_route_task(self, interface: Interface):
        logger.info(f'{interface.id_chat} Выбрал номер добавления маршрута - {interface.msg_user}')
        route: Route = self._down_routes.get_route(interface.msg_user)
        if not route.full_car:
            raise ExceptionMsg('Ошибка: Свободные места на рейс есть!\nВыберите другой!')
        self._down_routes.check_task_route(route.info_short)  # проверка рейс не на отслеживании у пользователя
        try:
            StepsTasks.add_task_user(interface.id_chat, self._date_choose, self._id_city_from, self._id_city_to,
                                     route.info_short, route.time_from)
            #interface.b_end = True
            interface.msg_info.text = f'Создано задание на слежение\n{route.info}.'
            self._s4_city_to_print(interface)
            StepsTasks().s1_view_active(interface)  # обновить список заданий
        except Exception as e:
            logger.warning(f'Ошибка: Создания задания! Повторите ввод номера рейса! {str(e)}')
            raise ExceptionMsg('Ошибка: Создания задания! Повторите ввод номера рейса!')



