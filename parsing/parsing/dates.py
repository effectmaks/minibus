from datetime import datetime, timedelta
from parsing.exception import ExceptionMsg


class Dates:
    """
    Даты по которым можно найти маршруты
    """
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
        return f"{date_now.strftime(self._FORMAT_DATE)} - {week}"


if __name__ == '__main__':
    dates = Dates()
    print(dates.get_short_info('25.02.2023'))
