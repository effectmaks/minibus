import telebot
from telebot import types
from parsing.routestep import StepsFind
from typing import Dict
from parsing.taskstep import StepsTasks, TimeTask
from parsing.msguser import MsgUser
from parsing.exception import ExceptionMsg
from parsing.interface import Interface
from parsing.log import logger
import platform
import enum

from dotenv import load_dotenv
import os

BASE_PATH = '../secrets.env'
if platform.system().startswith('L'):
    BASE_PATH = 'secrets.env'  # если запускать с Linux python3 start.py
load_dotenv(BASE_PATH)


class User:
    pass

CMD_FIND = '/find'
CMD_TASK = '/task'
CMD_START = '/start'
CMD_HELP = '/help'
CMDS = [CMD_FIND, CMD_TASK, CMD_START, CMD_HELP]

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

steps_find_dict: Dict[int, StepsFind] = {}
steps_task_dict: Dict[int, StepsTasks] = {}


def run_command(message):
    """
    Принять сообщение с "/" команда
    """
    if not message.text in CMDS:
        return
    if message.text == CMD_FIND:
        send_route(message)
    elif message.text == CMD_TASK:
        send_task(message)
    elif message.text == CMD_START:
        send_start(message)
    elif message.text == CMD_HELP:
        interface = Interface.get(message.chat.id)
        delete_msg_cmd(interface)
        delete_list_msg(interface)
        send_help(message)
    return True


@bot.message_handler(commands=['start'])
def send_start(message):
    interface = Interface.get(message.chat.id)
    interface.mode = Interface.Mode.NONE
    bot.send_message(message.chat.id, f'Привет! Я умею отслеживать освободившиеся места '
                                      f'маршрутного такси - и могу уведомить о появлении свободного места!'
                                      f' {CMD_HELP} - как использовать бот.\n')
    send_task(message)
    TimeTask.add_name(f'{message.chat.id}-{message.text}')


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, f"Список команд:\n"
                              f"{CMD_FIND} - Создание слежения рейса\n"
                              f"{CMD_TASK} - Просмотр и удаление слежений\n"
                              f"{CMD_HELP} - Список команд\n"
                              f"{CMD_START} - Приветствие бота")


@bot.message_handler(commands=['task'])
def send_task(message):
    """
    Вопрос задания(слежения) для удаления
    """
    chat_id = message.chat.id
    steps_task_dict[chat_id] = StepsTasks()
    interface = Interface.get(chat_id)
    interface.mode = Interface.Mode.TASK
    interface.msg_user = message.text
    delete_msg_cmd(interface)
    delete_msg_step(interface)
    delete_list_msg(interface)
    steps_task_dict[chat_id].s1_view_active_task(interface)
    send_message_func(interface, s2_task)
    TimeTask.add_name(f'{message.chat.id}-{message.text}')


def s2_task(message):
    chat_id = message.chat.id
    func_step = steps_task_dict[chat_id].s2_delete_task
    bot_step(message, func_step, s2_task, s2_task)


@bot.message_handler(commands=['find'])
def send_route(message):
    """
    Первый шаг для добавления маршрута в задание(слежение)
    """
    chat_id = message.chat.id
    steps_find_dict[chat_id] = StepsFind()
    interface = Interface.get(chat_id)
    interface.mode = Interface.Mode.ROUTE
    interface.msg_user = message.text
    delete_msg_cmd(interface)
    delete_msg_step(interface)
    delete_list_msg(interface)
    steps_find_dict[chat_id].s1_date_print_find(interface)
    send_message_func(interface, s2_find)
    TimeTask.add_name(f'{message.chat.id}-{message.text}')


def s2_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s2_date_check_find
    bot_step(message, func_step, s2_find, s3_find)


def s3_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s3_city_from_print_find
    bot_step(message, func_step, s3_find, s4_find)


def s4_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s4_city_to_print_find
    bot_step(message, func_step, s4_find, s5_find)


def s5_find(message):
    chat_id = message.chat.id
    func_step = steps_find_dict[chat_id].s5_route_find
    bot_step(message, func_step, s5_find, s5_find)  # зациклил


def bot_step(message, func_step, func_now, func_next):
    """
    Проверка даты и вопрос город
    """
    chat_id = message.chat.id
    interface = Interface.get(chat_id)
    try:
        if run_command(message):
            return
        delete_message(chat_id, message.id)
        delete_msg_step(interface)
        interface.msg_user = message.text
        func_step(interface)
    except ExceptionMsg as e:
        interface.msg_info.text = str(e)
        send_message_func(interface, func_now)
        return
    except Exception as e:
        logger.error('Ошибка: Разбираемся!', exc_info=True)
        interface.msg_info.text = 'Ошибка: Разбираемся!'
        send_message_func(interface, func_now)
        return
    #if interface.mode == Interface.Mode.ROUTE:
    #delete_list_msg(interface)
    send_message_func(interface, func_next)


def send_list_task(interface: Interface):
    """
    Отослать список заданий
    """
    if interface.list_task.have:
        if interface.list_task.id == 0:
            msg_bot = bot.send_message(interface.id_chat, interface.list_task.text)
        else:
            msg_bot = bot.edit_message_text(interface.list_task.text, interface.id_chat, interface.list_task.id)
        interface.list_task.have = False
        interface.list_task.id = msg_bot.id
        interface.msg_bot_last = msg_bot
        return msg_bot.id


def send_list_routes(interface: Interface):
    """
    Отослать список заданий
    """
    if interface.list_routes.have:
        if interface.list_routes.id == 0:
            msg_bot = bot.send_message(interface.id_chat, interface.list_routes.text)
        else:
            msg_bot = bot.edit_message_text(interface.list_routes.text, interface.id_chat, interface.list_routes.id)
        interface.list_routes.have = False
        interface.list_routes.id = msg_bot.id
        interface.msg_bot_last = msg_bot
        return msg_bot.id


def send_msg_do_task(interface: Interface):
    """
    Отослать действие пользователю
    """
    if interface.msg_do.have:
        if interface.msg_do.id == 0:
            msg_bot = bot.send_message(interface.id_chat, interface.msg_do.text)
        else:
            msg_bot = bot.edit_message_text(interface.msg_do.text, interface.id_chat, interface.msg_do.id)
        interface.msg_do.have = False
        interface.msg_do.id = msg_bot.id
        interface.msg_bot_last = msg_bot
        return msg_bot.id


def send_list_msg_routes(interface: Interface):
    """
    Отослать список с информацией(даты, пункты выезда)
    """
    if interface.list_msg.have:
        if interface.list_msg.id == 0:
            msg_bot = bot.send_message(interface.id_chat, interface.list_msg.text)
        else:
            msg_bot = bot.edit_message_text(interface.list_msg.text, interface.id_chat, interface.list_msg.id)
        interface.list_msg.have = False
        interface.list_msg.id = msg_bot.id
        interface.msg_bot_last = msg_bot
        return msg_bot.id


def send_msg_info_task(interface: Interface):
    """
    Отослать ошибку
    """
    if interface.msg_info.text:
        msg_bot = bot.send_message(interface.id_chat, interface.msg_info.text)
        interface.msg_info.id = msg_bot.id
        interface.msg_bot_last = msg_bot
        return msg_bot.id


def send_message_func(interface: Interface, func_next):
    """
    Отправить сообщение и установить след функцию
    :param func: Функция на ответ пользователя
    """
    #if interface.mode == Interface.Mode.TASK:
    send_list_task(interface)
    send_list_routes(interface)
    send_msg_do_task(interface)
    send_msg_info_task(interface)
    if interface.mode == Interface.Mode.ROUTE:
        send_list_msg_routes(interface)

    if func_next and not interface.b_end:
        bot.register_next_step_handler(interface.msg_bot_last, func_next)

    if interface.b_end:
        interface.mode = Interface.Mode.NONE
        bot.register_next_step_handler(interface.msg_bot_last, run_command)



def delete_message(id_chat, id_msg_delete):
    """
    Удалить сообщение в чате
    :param id_chat:
    :param id_msg_delete:
    """
    try:
        bot.delete_message(id_chat, id_msg_delete)
    except Exception as e:
         logger.error(f'Ошибка удаления сообщения {id_chat} msg {id_msg_delete}', exc_info=True)


def delete_msg_cmd(interface: Interface):
    """
    Новая команда, удалить сообщения старые
    """
    for id_msg in interface.get_delete_msg_cmd():
        delete_message(interface.id_chat, id_msg)


def delete_list_msg(interface: Interface):
    """
    Удалить лист с информацией (даты, пункты)
    """
    for id_msg in interface.get_delete_list_msg():
        delete_message(interface.id_chat, id_msg)


def delete_msg_step(interface: Interface):
    """
    Удалить старые сообщения перед следующим шагом
    """
    for id_msg in interface.get_delete_msg_step():
        delete_message(interface.id_chat, id_msg)


@bot.message_handler(content_types=['text'])
def msg_user(message):
    if run_command(message):
        return
    send_help(message)
    TimeTask.add_name(f'{message.chat.id}-{message.text}')


@bot.callback_query_handler(func=lambda call: True)
def click_button(call):
    MsgUser().answer_user(call.from_user.id, call.data)
    TimeTask.add_name(f'{call.from_user.id}-{call.data}')


bot.enable_save_next_step_handlers(delay=2)

logger.info("Start")
bot.infinity_polling()

# msg = bot.reply_to(message, steps_find_dict[chat_id].s1_date()) ответ на сообщение пользователя
