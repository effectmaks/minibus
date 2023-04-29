from celery import Celery
import logging
from celery.handlers.logging import TaskHandler
from dotenv import load_dotenv
from parsing.log import logger, log_format, FILE_PATH, level
import os

load_dotenv('secrets.env')

CELERY_REDIS_HOST = 'localhost'
CELERY_REDIS_PORT = '6379'
CELERY_BROKER_URL = 'redis://' + CELERY_REDIS_HOST + ':' + CELERY_REDIS_PORT + '/0'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = 'redis://' + CELERY_REDIS_HOST + ':' + CELERY_REDIS_PORT + '/0'


app: Celery = Celery('parsing', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
app.autodiscover_tasks(['parsing'])


app.conf.beat_schedule = {
    'print_test-5-seconds': {
        'task': 'print_test',
        'schedule': 10.0,
    },
    'send_msg-30-seconds': {
        'task': 'send_msg',
        'schedule': 30.0,
    },
    'check_task-60*5-seconds': {
        'task': 'check_task',
        'schedule': 60 * 3,
    },
    'download_id_cities-60*60*24-seconds': {
        'task': 'download_id_cities',
        'schedule': 60 * 60 * 24,
    },
}

task_handler = TaskHandler()
task_handler.setLevel(level)
logger.addHandler(task_handler)
