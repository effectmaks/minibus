import telebot
from telebot import types
from parsing.main import StepsFind
from typing import Dict
from parsing.message import MsgAnswer
from parsing.tasks_base import StepsTasks
from parsing.msguser import MsgUser
from parsing.tasks_base import TimeTask
import platform

import enum

from dotenv import load_dotenv
import os

BASE_PATH = '../secrets.env'
if platform.system().startswith('L'):
    BASE_PATH = 'secrets.env'  # если запускать с Linux python3 start.py
load_dotenv(BASE_PATH)


class ChatMode(enum.Enum):
    NONE = 0
    FIND = 1
    TASK = 2


class User:
    def __init__(self):
        self.mode = ChatMode.NONE

CMD_FIND = '/find'
CMD_TASK = '/task'
CMD_START = '/start'
CMD_HELP = '/help'
CMDS = [CMD_FIND, CMD_TASK, CMD_START, CMD_HELP]

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

user_dict = {}
steps_find_dict: Dict[int, StepsFind] = {}
steps_task_dict: Dict[int, StepsTasks] = {}
users_dict: Dict[int, User] = {}

message_id_main: int


def run_command(message):
    if not message.text in CMDS:
        return
    if message.text == CMD_FIND:
        send_find(message)
    elif message.text == CMD_TASK:
        send_task(message)
    elif message.text == CMD_START:
        send_start(message)
    elif message.text == CMD_HELP:
        send_help(message)
    return True


@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(message.chat.id, f'Привет! Я умею отслеживать освободившиеся места '
                                      f'маршрутного такси - и могу уведомить о появлении свободного места!'
                                      f' {CMD_HELP} - как использовать бот.\n')
    TimeTask.add_name(message.chat.id)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, f"Список команд:\n"
                              f"{CMD_FIND} - Создание слежения рейса\n"
                              f"{CMD_TASK} - Просмотр и удаление слежений\n"
                              f"{CMD_HELP} - Список команд\n"
                              f"{CMD_START} - Приветствие бота")
    TimeTask.add_name(message.chat.id)


@bot.message_handler(commands=['task'])
def send_task(message):
    """
    Вопрос задания
    """
    user = User()
    user.mode = ChatMode.TASK
    chat_id = message.chat.id
    user_dict[chat_id] = user
    steps_task_dict[chat_id] = StepsTasks()
    msg: MsgAnswer = steps_task_dict[chat_id].s1_view_active(chat_id)
    send_message_func(chat_id, msg, s2_task)
    TimeTask.add_name(message.chat.id)

def s2_task(message):
    chat_id = message.chat.id
    func_step = steps_task_dict[chat_id].s2_delete_task
    bot_step(message, func_step, s2_task, None)


@bot.message_handler(commands=['find'])
def send_find(message):
    """
    Вопрос дата
    """
    user = User()
    user.mode = ChatMode.FIND
    user_dict[message.chat.id] = user
    chat_id = message.chat.id
    steps_find_dict[chat_id] = StepsFind()
    msg: MsgAnswer = steps_find_dict[chat_id].s1_date_print()
    send_message_func(chat_id, msg, s2_find)
    TimeTask.add_name(message.chat.id)


def bot_step(message, func_step, func_now, func_next):
    """
    Проверка даты и вопрос город
    """
    chat_id = message.chat.id
    delete_message(chat_id, message.id)
    try:
        if run_command(message):
            return
        msg: MsgAnswer = func_step(chat_id, message.text)
    except Exception as e:
        send_message_func(chat_id, MsgAnswer('', str(e)), func_now)
        return
    send_message_func(chat_id, msg, func_next)


def s2_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s2_date_check
    bot_step(message, func_step, s2_find, s3_find)


def s3_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s3_city_from_print
    bot_step(message, func_step, s3_find, s4_find)


def s4_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s4_city_to_print
    bot_step(message, func_step, s4_find, s5_find)


def s5_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s5_route_task
    bot_step(message, func_step, s5_find, s4_find)  # зациклил


def send_message_func(chat_id, msg: MsgAnswer, func):
    """
    Отправить сообщение и установить след функцию
    :param msg_text: Текст сообщения
    :param func: Функция на ответ пользователя
    """

    user: User = user_dict.get(chat_id)
    if not user:
        return
    if user.mode == ChatMode.FIND:
        st_fc = steps_find_dict[chat_id]
    if user.mode == ChatMode.TASK:
        st_fc = steps_task_dict[chat_id]
    msg_bot = 0
    if st_fc.message_id_delete != 0:
        delete_message(chat_id, st_fc.message_id_delete)
        st_fc.message_id_delete = 0
    if msg.user:
        msg_bot = bot.send_message(chat_id, msg.user)
    if st_fc.b_end:
        if user.mode == ChatMode.FIND:
            delete_message(chat_id, st_fc.message_id_main)
        bot.send_message(chat_id, msg.bot)
        return
    if st_fc.message_id_main and not msg.bot.startswith('Ошибка'):
        msg_bot = bot.edit_message_text(msg.bot, chat_id, st_fc.message_id_main)
    else:
        msg_bot = bot.send_message(chat_id, msg.bot)
        if st_fc.message_id_main == 0:
            st_fc.message_id_main = msg_bot.id
    if msg.bot.startswith('Ошибка'):
        st_fc.message_id_delete = msg_bot.id
    if func:
        bot.register_next_step_handler(msg_bot, func)


def delete_message(id_chat, id_msg_delete):
    """
    Удалить сообщение в чате
    :param id_chat:
    :param id_msg_delete:
    """
    try:
        bot.delete_message(id_chat, id_msg_delete)
    except Exception as e:
        print(f'Ошибка удаления сообщения chat {id_chat} msg {id_msg_delete} {str(e)}')


@bot.message_handler(content_types=['text'])
def msg_user(message):
    if run_command(message):
        return
    send_help(message)
    TimeTask.add_name(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def click_button(call):
    MsgUser().answer_user(call.from_user.id, call.data)
    TimeTask.add_name(call.from_user.id)




# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
#bot.load_next_step_handlers()
print("Start")
bot.infinity_polling()

# msg = bot.reply_to(message, steps_find_dict[chat_id].s1_date()) ответ на сообщение пользователя