import datetime

from peewee import JOIN
from parsing.log import logger
from parsing.base.usertask import Usertask
from parsing.base.task import Task
from parsing.routestep import StepsTasks
from parsing.dates import Dates

import telebot
from telebot import types
import os
import platform
from dotenv import load_dotenv


class MsgUser:
    """
    При появлении рейса оповестить пользователя
    """

    def __init__(self):
        self._API_TOKEN = os.getenv('API_TOKEN')
        self._DELETE_TASK_MSG = 'Delete_task'
        self._bot = None

    def send_msg_have_place(self):
        """
        Отправляет пользователю сообщение, если появились свободные места
        """
        logger.info('CELERY Места для пользователя появились?')
        tasks_obj = StepsTasks()
        usertasks = tasks_obj.get_tasks_have_place()
        if usertasks:
            for usertask in usertasks:
                task = tasks_obj.create_info_task(usertask.id_chat, usertask.id, usertask.task.date,
                                                  usertask.task.id_from_city, usertask.task.id_to_city,
                                                  usertask.task.info)
                time_off = Dates.create_date_time_str(datetime.datetime.now())
                time_diff_str = Dates.get_diff_time_str(usertask.task.time_on, time_off)
                create_time_str = Dates.create_time_str(usertask.task.time_on)
                msg_place = f'ПОЯВИЛОСЬ место в {create_time_str} час'
                msg_free = f'СВОБОДНО ({time_diff_str})'
                logger.info(f'CELERY {usertask.id_chat} Появилось место {task.info}')
                msg = self._send_button_delete(usertask.id_chat, f'🟢{msg_place}\n🟢{msg_free}\n───────────👀────\n🟢{task.info}', usertask.id)
                tasks_obj.update_task_msg_delete(usertask.id, msg.id)
                if usertask.id_msg_delete:
                    self._delete_message(usertask.id_chat, usertask.id_msg_delete,
                                         f'CELERY id_chat {usertask.id_chat} Удалено сообщение ID {usertask.id_msg_delete}')
        else:
            logger.info('CELERY Нет маршрутов со свободными местами.')

    def _send_button_delete(self, id_chat, text, id_base_task):
        """
        отправить сообщение с кнопкой
        :param id_chat:
        :param text:
        :return:
        """
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Удалить слежение!", callback_data=f'{self._DELETE_TASK_MSG}{id_base_task}')
        markup.add(button1)
        msg = self._send_message(id_chat, text, markup)
        return msg

    def _command_delete_msg(self, id_chat, id_base_user_task, msg):
        """
        Команда удалить сообщение с уведомлением, если оно есть, и отправить сообщение что оно удалено
        """
        self._delete_task(id_chat, id_base_user_task, msg)
        id_msg_delete = StepsTasks.get_msg_delete(id_base_user_task)
        if id_msg_delete:
            self._delete_message(id_chat, id_msg_delete,
                                 f'{id_chat} Удалено сообщение ID {id_msg_delete}')

    def answer_user(self, id_chat, text: str):
        """
        Нажата кнопка удалить слежение.
        Удаляем кнопку и слежение пользователя из базы
        :param id_chat:
        :param text:
        """
        logger.info(f'{id_chat} Кнопка "Удалить уведомление" "{text}"')
        if not text.startswith(self._DELETE_TASK_MSG):
            logger.error(f'{id_chat} Нажата кнопка удалить уведомление, должно начинаеться с "{self._DELETE_TASK_MSG}"')
            return
        id_base_user_task = text.replace(self._DELETE_TASK_MSG, '')
        self._command_delete_msg(id_chat, id_base_user_task, "❌Слежение удалено❌\n")

    def _delete_task(self, id_chat, id_base_user_task, msg_text):
        """
        Выслать сообщение удалено задание по ID usertask и удалить его с базы у пользователя
        """
        usertasks = StepsTasks.get_tasks_have_place_id(id_base_user_task)
        if not usertasks:
            logger.error(f'{id_chat} Нет в базе информации для ID_usertask{id_base_user_task}')
            return
        user_task = usertasks[0]
        task = StepsTasks().create_info_task(user_task.id_chat, user_task.id, user_task.task.date,
                                             user_task.task.id_from_city, user_task.task.id_to_city,
                                             user_task.task.info)
        msg = self._send_message(user_task.id_chat, f'{msg_text}🟡{task.info}', None)
        StepsTasks.delete_usertask(id_base_user_task)

    def _delete_message(self, id_chat, id_msg_delete, msg):
        """
        Удалить сообщение в чате
        :param id_chat:
        :param id_msg_delete:
        """
        try:
            if not self._bot:
                self._create_link_bot()
            self._bot.delete_message(id_chat, id_msg_delete)
            logger.info(msg)
        except Exception as e:
            logger.error(f'Ошибка удаления сообщения chat {id_chat} msg {id_msg_delete}', exc_info=True)

    def _send_message(self, id_chat, text, markup):
        """
        Отправить сообщение пользователю
        """
        try:
            if not self._bot:
                self._create_link_bot()
            if markup:
                msg = self._bot.send_message(id_chat, text, reply_markup=markup)
            else:
                msg = self._bot.send_message(id_chat, text)
            logger.info(f'CELERY {id_chat} Отправлено сообщение ID {msg.id}')
            return msg
        except Exception as e:
            logger.error(f'Ошибка отправки сообщения chat {id_chat} msg {text}', exc_info=True)

    def _create_link_bot(self):
        """
        Создать связь с ботом
        :return:
        """
        self._bot = telebot.TeleBot(self._API_TOKEN)

    def send_msg_place_off(self):
        """
        Если не успел удалить уведомление, а место пропало, отослать сообщение о пропуске
        """
        logger.info('CELERY Если не успел удалить уведомление, а место пропало, отослать сообщение о пропуске')
        tasks_obj = StepsTasks()
        usertasks = self._get_tasks_place_off()
        if usertasks:
            for usertask in usertasks:
                task = tasks_obj.create_info_task(usertask.id_chat, usertask.id, usertask.task.date,
                                                  usertask.task.id_from_city, usertask.task.id_to_city,
                                                  usertask.task.info)
                time_diff_str = Dates.get_diff_time_str(usertask.task.time_on, usertask.task.time_off)
                create_time_str = Dates.create_time_str(usertask.task.time_on)
                logger.info(f'CELERY {usertask.id_chat} Место снова занято {task.info}')
                msg_place = f'Место освободилось в {create_time_str} час'
                msg_free = f'{time_diff_str} было свободно'
                msg = self._send_message(usertask.id_chat, f'😕{msg_place}\n😢{msg_free}\n───────────👀────\n'
                                                           f'🟡{task.info}', None)

                tasks_obj.update_task_msg_delete(usertask.id, "")
                if usertask.id_msg_delete:
                    self._delete_message(usertask.id_chat, usertask.id_msg_delete,
                                         f'CELERY id_chat {usertask.id_chat} Удалено сообщение ID {usertask.id_msg_delete}')
        else:
            logger.info('CELERY Нет маршрутов со снова занятыми местами.')

    def _get_tasks_place_off(self):
        """
        Выгрузка заданий с рейсами, места которых снова заняты
        :return:
        """
        try:
            logger.debug(f'Выгрузка заданий c рейсами, места которых снова заняты')
            return Usertask.select()\
                           .join(Task) \
                            .where(Task.have_place == False,
                                   Task.time_on != "",
                                   Task.time_off != "",
                                   Usertask.id_msg_delete != "") \
                            .order_by(Task.date).execute()
        except Exception as e:
            raise Exception(f'Ошибка выгрузки c базы. {str(e)}')

    def _get_tasks_delete(self):
        """
        Выгрузка заданий которые просрочены и их надо удалить
        :return:
        """
        try:
            logger.debug(f'Выгрузка заданий которые просрочены и их надо удалить')
            date_now_str = Dates.create_date_str(datetime.datetime.now())
            date_time_str = Dates.create_date_time_str(datetime.datetime.now())
            time_now_str = Dates.create_time_str(date_time_str)
            print(time_now_str+':00')
            return Task.select(Usertask.id, Usertask.id_chat, Task.id.alias('id_task')) \
                       .join(Usertask, JOIN.LEFT_OUTER) \
                       .where(Task.date == date_now_str,
                              Task.time_from < time_now_str+':00')\
                       .order_by(Task.id) \
                       .dicts()
        except Exception as e:
            raise Exception(f'Ошибка выгрузки c базы. {str(e)}')

    def delete_old_tasks(self):
        """
        Удалить старые слежения, и сообщить это пользователю
        """
        usertasks = self._get_tasks_delete()
        task_delete_prev = 0
        for usertask in usertasks:
            if usertask.get('id_chat') and usertask.get('id'):
                logger.info(f'CELERY {usertask.get("id_chat")} Просрочено, удалить слежение пользователя')
                self._command_delete_msg(usertask.get('id_chat'), usertask.get('id'),
                                         "❌Слежение удалено❌\n🚙Маршрутка выехала\n")
            if task_delete_prev != usertask.get('id_task'):
                StepsTasks.delete_task(usertask.get('id_task'))
                logger.info(f'CELERY Удалено задание task ID {usertask.get("id_task")}')
                task_delete_prev = usertask.get('id_task')


if __name__ == '__main__':
    BASE_PATH = '../secrets.env'
    if platform.system().startswith('L'):
        BASE_PATH = 'secrets.env'  # если запускать с Linux python3 start.py
    load_dotenv(BASE_PATH)
    MsgUser().delete_old_tasks()


    #from parsing.taskstep import RunTask
    #RunTask._update_task_have_place("08.03.2023", 5, 23, "(12:15-14:35)", True)
    #MsgUser().send_msg_have_place()  # Новые сообщения для пользователя - появились места
    #MsgUser().send_msg_place_off()  # Если не успел удалить уведомление, а место пропало, отослать сообщение о пропуске
