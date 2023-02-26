class MsgAnswer:
    def __init__(self, user, bot):
        self.user: str = user
        self.bot: str = bot


class MsgControl:
    def __init__(self):
        self.message_id_main: int = 0
        self.message_id_delete: int = 0
        self.b_end = False


if __name__ == '__main__':
    import telebot
    API_TOKEN = '6086504885:AAH8j6GN0j7gL3iXzEUa5oX27C8cU4tYzR4'
    bot = telebot.TeleBot(API_TOKEN)
    msg = bot.send_message('481687938', '481687938')