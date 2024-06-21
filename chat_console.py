# listen to a canvas file , and make sure all content has response.
import os.path

from colorama import Fore, Back, Style

from Chat.chatutil import *
from chat_bot_util import *

USE_NERD_FONT = False


def process_ai_message(text_content):
    prefix = text_content[:PREFIX_LENGTH] if len(text_content) > PREFIX_LENGTH else text_content

    if ':' in prefix:
        message = create_system_message(text_content)
        return True, message
    return False, None


def read_config_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def _color_out(custom, txt):
    print(custom, end='')
    print(txt, end='')
    print(Style.RESET_ALL)


def system_out(txt):
    _color_out(Back.MAGENTA, txt)


def tips_out(txt):
    _color_out(Fore.CYAN, txt)


def user_out(txt):
    _color_out(Fore.GREEN, txt)


def file_out(txt):
    _color_out(Fore.YELLOW, txt)


def greet():
    system_out('(Q to quit.)  free any time. or ctrl + C finish. and make new chat.')


def bye():
    system_out('Exited. Tks for use. Thanks♪(･ω･)ﾉ')


def bold(text):
    return '\033[1m' + str(text) + '\033[0m'


class ConsoleChat:
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
            word = get_words(content)
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
            try:
                _role = dialog["role"]
                if msg.startswith('file:'):
                    file_out(f'+ {self.fm_name}: {msg[len("file:"):]}')
                    tips_out(f'{self.system_name}: {dialog["content"]}')
                elif _role == SYS_ROLE:
                    tips_out(f'{self.system_name}: {dialog["content"]}')
                else:
                    tips_out(f'{_role}: {dialog["content"]}')
            except:
                # user_out(mg)
                pass
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

    console_chat = ConsoleChat(user_tex, bot_tex, sys_tex, fm_tex)
    greet()
    while console_chat.running:
        try:
            console_chat.loop()
        except KeyboardInterrupt:
            # reset style on interrupt
            print(Style.RESET_ALL, end='')
            console_chat.new_dialog()
    bye()
