from parsing.msguser import MsgUser
from parsing.tasks import RunTask
from parsing.cities import DownloadCities


if __name__ == '__main__':
    #RunTask.check()  # Проверка может появились новые места
    MsgUser().send_msg_have_place()  # Новые сообщения для пользователя - появились места
    #DownloadCities().download_cities_from()  # Обновление ID остановок