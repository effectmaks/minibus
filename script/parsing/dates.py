from datetime import datetime, timedelta
from parsing.exception import ExceptionMsg


class Dates:
    """
    Даты по которым можно найти маршруты
    """
    _FORMAT_DATE_TIME = '%d.%m.%Y %H:%M:%S'
    _FORMAT_TIME = '%H:%M'
    _FORMAT_DATE = '%d.%m.%Y'

    def __init__(self):
        self.dict_days = dict()
        self._FORMAT_DATE = '%d.%m.%Y'
        self._dict_week = {5: 'СБ',
                     6: 'ВС',
                     0: 'ПН',
                     1: 'ВТ',
                     2: 'СР',
                     3: 'ЧТ',
                     4: 'ПТ', }

    @property
    def items(self):
        if self.dict_days:
            return [s for s in self.dict_days.values()]

    def have_list(self):
        date_now = datetime.now()
        days = list()
        days.append(self._get_day_str(date_now))
        for _ in range(6):
            date_now = date_now + timedelta(days=1)
            days.append(self._get_day_str(date_now))
        return '\n'.join(days)

    def get_short_info(self, datetime_str):
        datetime_d = datetime.strptime(datetime_str, self._FORMAT_DATE).date()
        week = self._get_week(datetime_d)
        return self._create_info_str(datetime_d, week)

    def _get_week(self, date_now):
        num = date_now.weekday()
        return self._dict_week.get(num)

    def _get_day_str(self, date_now):
        week = self._get_week(date_now)
        self.dict_days[int(date_now.strftime('%d'))] = date_now.strftime(self._FORMAT_DATE)
        return self._create_info_str(date_now, week)

    def get_day_dict(self, id):
        try:
            id_int = int(id)
        except Exception:
            raise ExceptionMsg('Ошибка: Введите число!')

        return self.dict_days.get(id_int)

    def _create_info_str(self, date_now, week):
        """
        Строка инфо для пользователя
        :param date_now:
        :param week:
        :return: инфо
        """
        return f"{week} {date_now.strftime(self._FORMAT_DATE)}"

    @classmethod
    def create_date_time_str(cls, date_now):
        """
        Дата и время в текстовом формате
        :param date_now:
        :return: Дата и время строка
        """
        return date_now.strftime(cls._FORMAT_DATE_TIME)

    @classmethod
    def create_date_str(cls, date_now):
        """
        Дата в текстовом формате
        :param date_now:
        :return: Дата и время строка
        """
        return date_now.strftime(cls._FORMAT_DATE)

    @classmethod
    def create_time_str(cls, datetime_str):
        """
        Время в текстовом формате
        :param date_now:
        :return: время строка
        """
        datetime_d = datetime.strptime(datetime_str, cls._FORMAT_DATE_TIME)
        return datetime_d.strftime(cls._FORMAT_TIME)

    @classmethod
    def get_diff_time_str(cls, time_on_str, time_off_str):
        """
        Дата и время в текстовом формате.
        Вычисляет разницу в часах и минутах
        :return: Разница времен строка
        """
        time_on = datetime.strptime(time_on_str, cls._FORMAT_DATE_TIME)
        time_off = datetime.strptime(time_off_str, cls._FORMAT_DATE_TIME)
        time_diff = time_off - time_on
        date_time_str = str(time_diff)
        date_time_str = date_time_str[-8:]
        hour = date_time_str[:2]
        min = date_time_str[-5:-3]
        hour = hour.replace(':', '')
        if hour == '0':
            return f'{min} мин'
        else:
            return f'{hour} час {min} мин'


if __name__ == '__main__':
    #print(Dates().get_short_info('25.02.2023'))
    #print(Dates.create_date_time_str(datetime.now()))
    #print(Dates.get_diff_time_str("5.03.2023 12:55:34", "5.03.2023 15:50:34", ))
    print(Dates.create_time_str("5.03.2023 12:55:34"))
