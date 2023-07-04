from parsing.log import logger
import requests
from bs4 import BeautifulSoup
import json
import enum
from parsing.exception import ExceptionMsg
from typing import List
from parsing.base.task import Task
from parsing.base.usertask import Usertask


class PlaceMode(enum.Enum):
    FROM = 1
    TO = 2


class Place:
    """
    Из container_html извлекает время и город выезда и приезда по маршруту
    """
    def __init__(self, container_html, mode: PlaceMode):
        """
        Заполнить поля время и город
        :param container_html: Страниуа с инфо маршрута
        :param mode: Режим FROM или TO
        """
        logger.debug('Объект время и место')
        route_html = self._get_route_html(container_html, mode)
        self._time: str = self._get_time_city(route_html, 'time')
        self._city: str = self._get_time_city(route_html, 'place')
        self._date: str = self._get_time_city(route_html, 'date')

    @property
    def time(self):
        return self._time

    @property
    def city(self):
        return self._city

    @property
    def date(self):
        return self._date

    def _get_time_city(self, route_html, str_time_place: str):
        """
        Извлекает время или место из HTML
        :param route_html: Часть с временем и местом
        :param route_html: Часть с временем и местом
        :return: Место или время
        """
        logger.debug('Извлекает время или место из HTML')
        part_html = route_html.find('div', class_=f'nf-route__{str_time_place}')
        if part_html is None:
            raise Exception(f'Ошибка. Не извлечь nf-route__{str_time_place}')
        return part_html.string

    def _get_route_html(self, container_html, mode: PlaceMode):
        """
        Извлекает часть HTML с временем и местом
        :param container_html: Информация о поездке
        :param mode: Режим извлечения
        :return: HTML время и место
        """
        logger.debug('Извлечь route_html')
        out = None
        if mode == PlaceMode.FROM:
            out = container_html.find('div', class_='nf-route__from')
        elif mode == PlaceMode.TO:
            out = container_html.find('div', class_='nf-route__to')
        if out is None:
            raise Exception(f'Ошибка. Не извлечь route__from/to! {container_html.string}')
        return out


class Route:
    def __init__(self):
        self.place_from: Place
        self.place_to: Place
        self.duration: str
        self._full_car: str = ""
        self.id: str = ""
        self.have_task: bool = False

    @property
    def full_car(self):
        return self._full_car

    @full_car.setter
    def full_car(self, full):
        if full == "нет свободных мест":
            self._full_car = ""
        else:
            self._full_car = full

    @property
    def info(self):
        close = '🟢'
        if self.have_task:
            close = "🟡"
        elif self._full_car:
            close = "🔴"
        return f'{self.id if int(self.id) > 9 else " " + self.id} : {close} ' \
               f'{self.place_from.time}-{self.place_to.time} ({self.duration})'

    @property
    def info_short(self):
        return f'({self.place_from.time}-{self.place_to.time})'

    @property
    def time_from(self):
        return f'{self.place_from.time}'

    @property
    def title(self):
        if self.place_from:
            return f'{self.place_from.date}\n{self.place_from.city} -> {self.place_to.city}'

    @property
    def have_place(self):
        if not self._full_car:
            return True


class DateRoute:
    def __init__(self, date, week):
        self.date: str = date
        self.week: str = week

    @property
    def info(self):
        return f'{self.date} - {self.week}'


class DownloadRoutes:
    """
    Скачивает информацию рейсов
    """
    def __init__(self, day, id_from, id_to, id_chat: int = 0):
        self._route_one: Route
        self._routes_list: List[Route] = list()
        self._dates_route: list = list()
        self._download_routes(day, id_from, id_to)
        self._day = day
        self._id_from = id_from
        self._id_to = id_to
        self._id_chat = id_chat

    @property
    def list(self):
        if self._id_chat:
            self._set_point_yellow(self._id_chat, self._day, self._id_from, self._id_to)
        return self._routes_list

    @property
    def dates_route(self):
        return self._dates_route

    def have_place(self, info):
        for r in self._routes_list:
            if r.info_short == info:
                return r.have_place

    def get_route(self, id):
        """
        Возвращает рейс по id
        :param id:
        :return:
        """
        for route in self._routes_list:
            if route.id == id:
                return route
        raise ExceptionMsg('Ошибка: Введите число из списка')

    def _download_routes(self, day, id_from, id_to):
        """
        Заполнить данные маршрута
        """
        try:
            logger.debug('Заполнить данные маршрута')
            page_html = self._get_page_html(day, id_from, id_to)
            self._parse_route(page_html)
        except ExceptionMsg as e:
            raise ExceptionMsg(str(e))
        except Exception as e:
            raise Exception(f"Ошибка! При переборе маршрутов {str(e)}")

    def _parse_route(self, page_html):
        """
        Заполнить время город время_пути доступность
        :param page_html: Страница ответа сервера с данными
        """
        list_routes_html = self._get_nf_route_html(page_html)
        count = len(list_routes_html)
        for nf_route_one_html, id in zip(list_routes_html, range(1, count + 1)):
            self._route_one = Route()
            self._parse_nf_route_one_html(nf_route_one_html)
            self._route_one.id = str(id)
            self._routes_list.append(self._route_one)

    def _parse_nf_route_one_html(self, nf_route_one_html):
        """
        Извлечь все данные о маршруте
        :param nf_route_one_html: HTML с полной информацией одного маршрута
        """
        try:
            container_html = self._get_container_html(nf_route_one_html)
            self._full_places_from_to(container_html)
            self._full_duration_full_car(container_html)
        except Exception as e:
            raise Exception(f'Ошибка извлечения информации о маршруте {str(e)}')

    def _get_page_html(self, day, id_from, id_to):
        """
        Запрос на сервер.
        Все части HTML с полной информацией всех маршрутов
        :return: HTML list
        """
        logger.debug('Части HTML с полной информацией всех маршрутов')
        response = requests.get(f'https://xn--90aiim0b.xn--80aa3agllaqi6bg.xn--90ais/schedules?'
                                f'station_from_id=0&station_to_id=0&'
                                f'city_from_id={id_from}&'
                                f'city_to_id={id_to}&'
                                f'date={day}&time=00%3A00&places=1')
        if response.status_code != 200:
            logger.warning(f'Ответ получен {response.status_code} {response.text}')
            raise Exception('Ошибка запроса на сервер ', response.status_code)
        logger.debug(f'Ответ получен {response.status_code}')
        logger.debug(f'Ответ получен {response.text}')
        data = json.loads(response.text)
        out = BeautifulSoup(data.get("html"), 'html.parser')
        if out is None:
            raise Exception('Ошибка, не получилось извлечь html')
        alert = out.find('div', class_='alert__content')
        if alert:
            alert_str = alert.string
            if alert_str.startswith('Рейсы'):
                raise ExceptionMsg(alert_str)
        return out

    def _get_nf_route_html(self, page_html):
        """
        Запрос на сервер.
        Все части HTML с полной информацией всех маршрутов
        :return: HTML list
        """
        logger.debug('Части HTML с полной информацией всех маршрутов')
        out = page_html.find_all('div', class_='nf-route')
        if out == []:
            raise Exception('Ошибка, не получилось извлечь nf-route')
        return out

    def _get_container_html(self, nf_route_one_html):
        """
        Извлечь container c инфо о маршруте
        :param nf_route_one_html: HTML с полной информацией одного маршрута
        :return: HTML container
        """
        logger.debug('Извлечь контайнер')
        container_html = nf_route_one_html.find('div', class_='nf-route__container')
        if container_html is None:
            raise Exception('Ошибка, не получилось извлечь nf-route__container', nf_route_one_html.string)
        return container_html

    def _full_places_from_to(self,container_html):
        """
        Извлечь время и город отъезда и приезда
        :param container_html: HTML с полной информацией одного маршрутов
        """
        logger.debug('Извлечь время и город выезда')
        self._route_one.place_from = Place(container_html, PlaceMode.FROM)
        logger.debug('Извлечь время и город приезда')
        self._route_one.place_to = Place(container_html, PlaceMode.TO)

    def _full_duration_full_car(self, container_html):
        """
        Извлечь время в пути и свободные места
        :param nf_route_one_html: HTML с полной информацией одного маршрутов
        """
        logger.debug('Извлечь время в пути и свободные места')
        info = container_html.find('div', class_='nf-route__content')
        if info is None:
            raise Exception('Не получилось извлечь route__content')
        logger.debug('Извлечь время в пути')
        duration = info.find('div', class_='nf-route__duration')
        if duration is None:
            raise Exception('Не получилось извлечь route__content')
        self._route_one.duration = duration.string
        logger.debug('Извлечь заполненность машины')
        full_car = info.find('div', class_='nf-route__time')
        if full_car:
            self._route_one.full_car = full_car.string

    def _set_point_yellow(self, id_chat, day, id_from, id_to):
        """
        Пометить маршруты, которые пользователь в этот день уже отслеживает
        """
        usertasks = Usertask.select().join(Task).where(Usertask.id_chat == id_chat,
                                                       Task.date == day,
                                                       Task.id_from_city == id_from,
                                                       Task.id_to_city == id_to).execute()
        for usertask in usertasks:
            self._set_have_task(usertask.task.info)

    def _set_have_task(self, info_short):
        """
        Пометить этот маршрут пользователь уже отслеживает
        """
        for route in self._routes_list:
            if route.info_short == info_short:
                route.have_task = True

    def check_task_route(self, info_short):
        """
        Проверка что пользователь выбрал, такое же задания на слежения
        :return:
        """

        logger.debug(f'Проверить что у пользователя нет этого задания выбрал пользователь')
        for route in self._routes_list:
            if route.info_short == info_short and route.have_task:
                raise ExceptionMsg('Ошибка: Это рейс вы уже отслеживаете!\nВведите другой номер рейса.')


if __name__ == '__main__':
    pass