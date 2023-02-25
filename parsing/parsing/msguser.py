from parsing.main import StepsTasks

import telebot
from telebot import types
import os


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
        print('Проверка появилось место во всех рейсах активных')
        tasks_obj = StepsTasks()
        tasks = tasks_obj.get_tasks_have_place()
        if tasks:
            for task_item in tasks:
                task = tasks_obj.create_info_task(task_item.id_chat, task_item.id, task_item.date,
                                                  task_item.id_from_city, task_item.id_to_city,
                                                  task_item.info)
                print(f'Появилось место для {task_item.id_chat} {task.info}')
                if task_item.id_msg_delete:
                    self._delete_message(task_item.id_chat, task_item.id_msg_delete)
                msg = self._send_button_delete(task_item.id_chat,
                                              '‼️Появилось место:‼️\n' + '🟢' + task.info, task_item.id)
                tasks_obj.update_task_msg_delete(task_item.id, msg.id)
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
        if not text.startswith(self._DELETE_TASK_MSG):
            return
        id_base_task = text.replace(self._DELETE_TASK_MSG, '')
        id_msg_delete = StepsTasks.get_msg_delete(id_chat, id_base_task)
        if id_msg_delete:
            self._delete_message(id_chat, id_msg_delete)
        StepsTasks.delete_task(id_base_task)

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
            print(f'Ошибка удаления сообщения chat {id_chat} msg {id_msg_delete}')

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
    MsgUser().send_msg_have_place()
