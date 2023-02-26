from parsing.routes import DownloadRoutes, Route
from parsing.cities import DownloadCities
from parsing.dates import Dates
from parsing.message import MsgAnswer, MsgControl
from parsing.exception import ExceptionMsg
from parsing.base.task import Task
from parsing.steptask import StepsTasks


class StepsFind(MsgControl):
    def __init__(self):
        super().__init__()
        self._dates = Dates()
        self._date_choose: str
        self._serv_cities: DownloadCities
        self._id_city_from: str
        self._id_city_to: str
        self._down_routes: DownloadRoutes

    def s1_date_print(self):
        """
        Список дат для поиска
        :return:
        """
        return MsgAnswer('', f'Даты рейсов маршрутки:\n──────────────👀──\n'
                             f'{self._dates.have_list()}\n──────👀──────────\n'
                             f'Введите дату (например: "18"):')

    def s2_date_check(self, chat_id, id):
        """
        Проверка выбранной даты
        :param id:
        :return:
        """
        self._date_choose = self._dates.get_day_dict(id)
        if not self._date_choose:
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        self._serv_cities = DownloadCities()
        return MsgAnswer(f'Дата: {self._dates.get_short_info(self._date_choose)}',
                         f'Список остановок выезда:\n─────👀───────────\n'
                         f'{self._serv_cities.cities()}\n────────👀────────\n'
                         f'Укажите пункт выезда (введите число):')

    def s3_city_from_print(self, chat_id, id):
        """
        Вопрос пункт выезда по ID пользователя
        :param id:
        :return:
        """
        s_out = self._serv_cities.download_cities_to(id)
        if not s_out:
            raise ExceptionMsg('Ошибка: Введите число из списка!')
        self._id_city_from = id
        city_choose = self._serv_cities.cities(id)
        return MsgAnswer(f'Из пункта: {city_choose}', f'Список остановок приезда:\n─────👀───────────\n{s_out}'
                                                      f'\n────────────👀────\nВведите конечный пункт\n(введите число):')

    def s4_city_to_print(self, chat_id, id):
        msg1: MsgAnswer = self._s4_city_to_check(chat_id, id)
        msg2: MsgAnswer = self._s4_city_to_print(chat_id, id)
        msg1.user += msg2.user
        msg1.bot += msg2.bot
        return msg1

    def _s4_city_to_check(self, chat_id, id):
        if id == self._id_city_from:
            raise ExceptionMsg('Ошибка: Не должны повторяться города!\nВведите число.')
        city_choose = self._serv_cities.cities(id)
        if not city_choose:
            raise ExceptionMsg('Ошибка: Введите число!')
        return MsgAnswer(f'В пункт: {city_choose}', '')

    def _s4_city_to_print(self, chat_id, id):
        self._id_city_to = id
        try:
            self._down_routes = DownloadRoutes(self._date_choose, self._id_city_from, self._id_city_to, id_chat=chat_id)
        except ExceptionMsg as e:
            self.b_end = True
            return MsgAnswer('', f'Ошибка: {str(e)}.')
        routes = self._down_routes.list
        if not routes:
            return MsgAnswer('', 'Ошибка: Нет данных!')
        s_out = '\n────────👀────────\nВыберите номер рейса для слежения: \n' \
                '🔴 - мест нет, можно отслеживать\n' \
                '🟡 - уже отслеживаете\n' \
                '🟢 - свободные билеты есть'
        s_out = f"Список рейсов на {self._dates.get_short_info(self._date_choose)}:\n─👀──────────────\n" + \
                '\n'.join([r.info for r in routes]) + s_out
        return MsgAnswer('', s_out)

    def s5_route_task(self, chat_id, id):
        route: Route = self._down_routes.get_route(id)
        if not route.full_car:
            raise ExceptionMsg('Ошибка: Свободные места на рейс есть!\nВыберите другой!')
        self._down_routes.check_task_route(route.info_short)  # проверка рейс не на отслеживании у пользователя
        try:
            StepsTasks.add_task_user(chat_id, self._date_choose, self._id_city_from, self._id_city_to,
                                     route.info_short, route.time_from)
            self.b_end = True
            return MsgAnswer('', f'Создано задание на слежение\n'
                                 f'{route.info}.')
        except ExceptionMsg as e:
            return MsgAnswer('', f'{str(e)}.')
        except Exception as e:
            print(f'Ошибка: Создания задания! Повторите ввод номера рейса! {str(e)}')
            raise ExceptionMsg('Ошибка: Создания задания! Повторите ввод номера рейса!')



