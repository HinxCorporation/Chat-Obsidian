# listen to a canvas file , and make sure all content has response.
import os.path

from Chat.chatutil import *
from PyChatBot.chat_on_consle import *


class ConsoleChat_Old:
    def __init__(self, user_name="You", bot_name="Bot", system_name='system', fm_name='file'):
        self.bot_msg: str = ''
        # utils needs an output method with a token input
        self.util = ChatUtil(self.console_out)
        self.running = True
        self.user_name = user_name
        self.bot_name = bot_name
        self.system_name = system_name
        self.fm_name = fm_name
        self.msg_stack = []

    def console_out(self, content: str):
        try:
            word = get_words_deep_seek_bot(content)
            print(word, end='', flush=True)
            self.bot_msg = self.bot_msg + word
        except Exception as ee:
            logging.error(f"Error processing content: {ee}")
            logging.error(content)
            print('-', end='', flush=True)

    def new_dialog(self):
        self.msg_stack = []
        clear_console()
        print('User clear,stack was cleared. New chat will begin.')
        greet()

    def chat(self, msg):
        msg = msg.strip()
        print(Fore.CYAN + self.bot_name + ': ', end='')
        self.util.chat(msg, context=self.msg_stack)
        print(Style.RESET_ALL)
        self.msg_stack.append(get_message(msg, USER_ROLE))
        self.msg_stack.append(get_message(self.bot_msg, BOT_ROLE))

    def loop(self):
        self.bot_msg = ''
        print('old chat bot method')
        print(Fore.LIGHTGREEN_EX + self.user_name + ': ', end='')
        msg = input()
        print(Style.RESET_ALL, end='')
        if not msg:
            return
        if msg in ["Q", 'q', "quit"]:
            self.running = False
            return
        if os.path.exists(msg):
            msg = f'file:{msg}'
        ai, dialog = process_ai_message(msg)
        if ai:
            out_ai_role_msg(self.fm_name, self.system_name, msg, dialog)
            self.msg_stack.append(dialog)
        else:
            self.chat(msg)
            term_width = int(os.get_terminal_size().columns / 3)
            tips_out(' - ' * term_width)


if __name__ == '__main__':

    user_tex = 'User'
    bot_tex = 'Bot'
    sys_tex = "System"
    fm_tex = 'file'
    USE_NERD_FONT = ""
    clear_console()

    try:
        config_file = 'config.ini'
        config_content = read_config_file(config_file)
        config = configparser.ConfigParser()
        config.read_string(config_content)

        USE_NERD_FONT = config.get('Console', 'use_nerd_font', fallback='false').lower() == 'true'
        if USE_NERD_FONT:
            user_tex = config.get('NERD', 'char_avatar', fallback=user_tex)
            bot_tex = config.get('NERD', 'char_bot', fallback=bot_tex)
            sys_tex = config.get('NERD', 'char_computer', fallback=sys_tex)
            fm_tex = config.get('NERD', 'char_folder', fallback=fm_tex)
            pass

    except Exception as e:
        print(f"An error occurred while reading the config file: {e}")

    if USE_NERD_FONT:
        system_out(f'{sys_tex} Now are using NERD font. enjoy.')
    else:
        system_out(f'{sys_tex} welcome')

    console_bot = ConsoleChat(None, user_tex, bot_tex, sys_tex, fm_tex)

    greet()
    while console_bot.running:
        try:
            console_bot.loop()
        except KeyboardInterrupt:
            # reset style on interrupt
            print(Style.RESET_ALL, end='')
            console_bot.new_dialog()
    bye()
