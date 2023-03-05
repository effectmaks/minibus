import requests
from bs4 import BeautifulSoup
import json
import enum
from parsing.base.cities import Cities


class DownloadCities:
    """
    Обновляет в базе информацию городов выезда (обновляет каждые 10 мин)
    """
    def __init__(self):
        self.id_cities: list

    def cities(self, id: str = '-'):
        if id == '-':
            cities = Cities.select().order_by(Cities.sort, Cities.name).execute()
            cities_list = [f'{c.id} - {c.name}' for c in cities]
            return '\n'.join(cities_list)
        else:
            cities = Cities.select().where(Cities.id == id).order_by(Cities.sort, Cities.name).execute()
            if not cities:
                return ""
            cities_list = [f'{c.name}' for c in cities]
            return ''.join(cities_list)

    def download_cities_from(self):
        """
        Заполнить города выезда и их id
        """
        try:
            print('Заполнить города выезда и их id')
            for option in self._get_city_from_id_html():
                id_city = option['value']
                name_city = option.string.strip()
                self._update_base_city(id_city=id_city, name_city=name_city)
        except Exception as e:
            raise Exception(f"Ошибка! При переборе городов {str(e)}")

    def download_cities_to(self, id):
        """
        Заполнить города приезда и их id
        """
        try:
            print('Заполнить города выезда и их id')
            cities = self._get_city_to_id_html(id)
            self._update_base_cities_to(cities)
            return self._sort_cities_values(cities)
        except Exception as e:
            raise Exception(f"Ошибка! При переборе городов {str(e)}")

    def _update_base_city(self, id_city, name_city):
        """
        Обновляет id и имя города или сохранить в базу
        :param option: HTML с городом
        """
        try:
            print(f'Обновить город ID: {id_city} {name_city}')
            if id_city in ['', '68', 68]:
                return
            data_count = Cities.select(Cities.name).where(Cities.id == id_city).count()
            if data_count == 0:
                Cities.create(name=name_city, id=id_city)
            else:
                Cities.update({Cities.name: name_city}).where(Cities.id == id_city).execute()
        except Exception as e:
            raise Exception(f'Ошибка извлечения информации о городе {str(e)}')

    def _get_city_from_id_html(self):
        """
        Запрос на сервер.
        Страница HTML
        :return: HTML list
        """
        print('Части HTML информацией городов')
        response = requests.get("https://xn--90aiim0b.xn--80aa3agllaqi6bg.xn--90ais/")
        if response.status_code != 200:
            raise Exception('Ошибка запроса на сервер ', response.status_code)
        print('Ответ получен', response.status_code)
        soup = BeautifulSoup(response.text, 'html.parser')
        select = soup.find('select', class_='js_city_from_id')
        out = select.find_all('option')
        if out is None:
            raise Exception('Ошибка, не получилось извлечь js_city_from_id')
        return out

    def _get_city_to_id_html(self, id):
        """
        Запрос на сервер.
        Страница HTML
        :return: HTML list
        """
        print('Части HTML городов приезда по ID')
        response = requests.get(f'https://xn--90aiim0b.xn--80aa3agllaqi6bg.xn--90ais/cities?city_from_id={id}')
        if response.status_code != 200:
            raise Exception('Ошибка запроса на сервер ', response.status_code)
        print('Ответ получен', response.status_code)
        data: dict = json.loads(response.text)
        out = data.values()
        if out is None:
            raise Exception('Ошибка, не получилось извлечь js_city_from_id')
        return out

    def _update_base_cities_to(self, cities):
        """
        Обновить в базе города и их id
        :param cities: Города лист
        """
        print("Обновить в базе города и их id")
        for city in cities:
            self._update_base_city(id_city=city.get('id'), name_city=city.get('name'))

    def _sort_cities_values(self, data):
        """
        Сортировка городов
        :param data: Города лист
        :return: Текст из списка городов
        """
        print("Сортировка городов")
        self._id_cities = [c.get('id') for c in data if c.get('id') != 68]
        cities = Cities.select().where(Cities.id << self._id_cities).order_by(Cities.sort, Cities.name).execute()
        cities_list = [f'{c.id} - {c.name}' for c in cities]
        self._check_result(self._id_cities, cities_list)
        return '\n'.join(cities_list)

    def _check_result(self, data_before, cities_after):
        """
        Совпадение количества городов до сортировки и после
        """
        count_before = len(data_before)  # Отнять прочерк
        count_after = len(cities_after)
        if count_before != count_after:
            raise Exception('Не совпадает количество до сортировки и после')


if __name__ == '__main__':
    DownloadCities().download_cities_from()  # Обновление ID остановок
