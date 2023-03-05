from typing import Dict
import enum


class ItemMsg:
    def __init__(self):
        self.have: bool = False
        self.text: str = ""
        self.id: int = 0


class Interface:
    """
    Сообщения которые отображаются пользователю
    """

    class Mode(enum.Enum):
        NONE = 0
        ROUTE = 1
        TASK = 2

    dict_users: Dict[int, 'Interface'] = {}

    def __init__(self, id_chat):
        self.id_chat: int = id_chat
        self.mode = self.Mode.NONE
        self.msg_user: str = ""
        self._list_task: ItemMsg = ItemMsg()
        self._list_routes: ItemMsg = ItemMsg()
        self._list_msg: ItemMsg = ItemMsg()
        self._msg_do: ItemMsg = ItemMsg()
        self.msg_info: ItemMsg = ItemMsg()
        self.b_end = False
        self._msg_bot_last = None

    @property
    def msg_do(self):
        return self._msg_do

    @msg_do.setter
    def msg_do(self, text):
        self._msg_do.text = text
        self._msg_do.have = True

    @property
    def list_msg(self):
        return self._list_msg

    @list_msg.setter
    def list_msg(self, text):
        self._list_msg.text = text
        self._list_msg.have = True

    @property
    def list_task(self):
        return self._list_task

    @list_task.setter
    def list_task(self, text):
        self._list_task.text = text
        self._list_task.have = True

    @property
    def list_routes(self):
        return self._list_routes

    @list_routes.setter
    def list_routes(self, text):
        self._list_routes.text = text
        self._list_routes.have = True

    @property
    def msg_bot_last(self):
       return self._msg_bot_last

    @msg_bot_last.setter
    def msg_bot_last(self, i):
        self._msg_bot_last = i

    def _clear_new_cmd(self):
        """
        Очистка при новой команде
        """
        self.b_end = False

    def _clear_item(self, item: ItemMsg):
        item.have = False
        item.text = ""
        item.id = 0

    def get_delete_msg_cmd(self):
        """
        Какие сообщения удалить при новой команде
        """
        if self.list_task.id != 0 and self.mode == self.Mode.TASK:
            yield self.list_task.id
            self._clear_item(self.list_task)
        if self.list_routes.id != 0:
            yield self.list_routes.id
            self._clear_item(self.list_routes)
        if self.list_msg.id != 0:
            yield self.list_msg.id
            self._clear_item(self.list_msg)
        if self.msg_do.id != 0:
            yield self.msg_do.id
            self._clear_item(self.msg_do)
        self._clear_new_cmd()

    def get_delete_msg_step(self):
        """
        Какие сообщения удалить перед следующим шагом
        """
        if self.msg_info.id != 0:
            yield self.msg_info.id
            self._clear_item(self.msg_info)

    def get_delete_list_msg(self):
        """
        Удалить лист с информацией(даты, пункты)
        """
        if self.list_msg.id != 0:
            yield self.list_msg.id
            self._clear_item(self.list_msg)

    @classmethod
    def get(cls, id_chat):
        """
        Возвращает интерфейс пользователя.
        Если нет - создает новый.
        """
        interface = cls.dict_users.get(id_chat)
        if interface:
            return interface
        interface = Interface(id_chat)
        cls.dict_users[id_chat] = interface
        return interface


if __name__ == '__main__':
    import telebot
    import platform
    from dotenv import load_dotenv
    import os

    BASE_PATH = '../secrets.env'
    if platform.system().startswith('L'):
        BASE_PATH = 'secrets.env'  # если запускать с Linux python3 start.py
    load_dotenv(BASE_PATH)
    API_TOKEN = os.getenv('API_TOKEN')
    bot = telebot.TeleBot(API_TOKEN)
    msg = bot.send_message('481687938', '481687938')