# listen to a canvas file , and make sure all content has response.

from colorama import Fore, Back, Style

from .chat_bot_util import *

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


def is_quit(msg):
    return msg in ["Q", 'q', "quit"]


def out_ai_role_msg(file_role, sys_role, msg, dialog):
    try:
        _role = dialog["role"]
        if msg.startswith('file:'):
            file_out(f'+ {file_role}: {msg[len("file:"):]}')
            tips_out(f'{sys_role}: {dialog["content"]}')
        elif _role == SYS_ROLE:
            tips_out(f'{sys_role}: {dialog["content"]}')
        else:
            tips_out(f'{_role}: {dialog["content"]}')
    except:
        # user_out(mg)
        pass
