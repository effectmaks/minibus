from parsing.log import logger
from parsing.celery import app
from parsing.msguser import MsgUser
from parsing.taskstep import RunTask
from parsing.citieshtml import DownloadCities


@app.task(name='print_test')
def print_test():
    logger.info('Celery work!')


@app.task(name='send_msg')  # 30 сек
def send_msg():
    logger.info('Новые сообщения для пользователя - появились места')
    MsgUser().send_msg_have_place()


@app.task(name='check_task')  # 60*5 сек
def check_task():
    logger.info('Проверка может появились новые места')
    RunTask.check()


@app.task(name='download_id_cities')  # 60*60*24 сек
def download_id_cities():
    logger.info('Обновление ID остановок')
    DownloadCities().download_cities_from()
