from parsing.main import StepsTasks

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
        print('Проверка - появилось место во всех рейсах активных')
        tasks_obj = StepsTasks()
        usertasks = tasks_obj.get_tasks_have_place()
        if usertasks:
            for usertask in usertasks:
                task = tasks_obj.create_info_task(usertask.id_chat, usertask.id, usertask.task.date,
                                                  usertask.task.id_from_city, usertask.task.id_to_city,
                                                  usertask.task.info)
                print(f'Появилось место для {usertask.id_chat} {task.info}')
                msg = self._send_button_delete(usertask.id_chat,
                                              '‼️Появилось место:‼️\n' + '🟢' + task.info, usertask.id)
                tasks_obj.update_task_msg_delete(usertask.id, msg.id)
                if usertask.id_msg_delete:
                    self._delete_message(usertask.id_chat, usertask.id_msg_delete)  # удалить старое сообщение
        else:
            print('Нет маршрутов с свободными местами.')

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

    def answer_user(self, id_chat, text: str):
        """
        Нажата кнопка удалить слежение.
        Удаляем кнопку и слежение пользователя из базы
        :param id_chat:
        :param text:
        """
        if not text.startswith(self._DELETE_TASK_MSG):
            return
        id_base_user_task = text.replace(self._DELETE_TASK_MSG, '')
        id_msg_delete = StepsTasks.get_msg_delete(id_base_user_task)
        if id_msg_delete:
            self._delete_message(id_chat, id_msg_delete)
            StepsTasks.delete_task(id_base_user_task)

    def _delete_message(self, id_chat, id_msg_delete):
        """
        Удалить сообщение в чате
        :param id_chat:
        :param id_msg_delete:
        """
        try:
            if not self._bot:
                self._create_link_bot()
            self._bot.delete_message(id_chat, id_msg_delete)
        except Exception as e:
            raise Exception(f'Ошибка удаления сообщения chat {id_chat} msg {id_msg_delete} {str(e)}')

    def _send_message(self, id_chat, text, markup):
        if not self._bot:
            self._create_link_bot()
        return self._bot.send_message(id_chat, text, reply_markup=markup)

    def _create_link_bot(self):
        """
        Создать связь с ботом
        :return:
        """
        self._bot = telebot.TeleBot(self._API_TOKEN)


if __name__ == '__main__':
    BASE_PATH = '../secrets.env'
    if platform.system().startswith('L'):
        BASE_PATH = 'secrets.env'  # если запускать с Linux python3 start.py
    load_dotenv(BASE_PATH)
    MsgUser().send_msg_have_place()  # Новые сообщения для пользователя - появились места
