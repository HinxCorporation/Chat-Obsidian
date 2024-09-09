from PyAissistant.Extension.ai_extension import ai_exposed_function
from PyAissistant.PyChatBot.chat_api import ChatBot
from PyAissistant.PyChatBot.deep_seek_bot import DeepSeekBot

from .console_chat_extension import *
from ..ConsoleChatBot import ConsoleChatBot


# from .deep_seek_bot import *


class ConsoleChat:

    @staticmethod
    @ai_exposed_function
    def write_file(relative_path, text_content):
        """
        method exposed to Ai assistant, writes text content to a file in the workspace
        :param relative_path: relative path to the file from the workspace root
        :param text_content: text content to be written to the file
        :return: success message
        """
        relative_path = os.path.join("ignore_AI_Workspace", relative_path)
        full_path = os.path.abspath(relative_path)
        if not os.path.exists(os.path.dirname(full_path)):
            os.makedirs(os.path.dirname(full_path))
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        return f"File {relative_path} created successfully."

    @staticmethod
    @ai_exposed_function
    def read_file(relative_path):
        """
        method exposed to Ai assistant, reads text content from a file in the workspace
        :param relative_path: relative path to the file from the workspace root
        :return: text content of the file
        """
        relative_path = os.path.join("ignore_AI_Workspace", relative_path)
        full_path = os.path.abspath(relative_path)
        if not os.path.exists(full_path):
            return f"File {relative_path} does not exist."
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    def __init__(self, user_name="You", bot_name="Bot", system_name='system', fm_name='file'):
        self.bot_msg: str = ''
        # utils needs an output method with a token input
        self.bot: ChatBot = ConsoleChatBot(post_words=self.print_console_word)

        self.running = True
        self.user_name = user_name
        self.bot_name = bot_name
        self.system_name = system_name
        self.fm_name = fm_name

    # this is the example of how to expose a function to Ai assistant
    @ai_exposed_function
    def ai_get_bot_name(self):
        """
        method exposed to Ai assistant , returns current bot name
        """
        return self.bot_name

    @staticmethod
    def print_function_call_result( result):
        print(Fore.GREEN + result)
        print(Fore.LIGHTGREEN_EX)

    def print_console_word(self, word: str):
        print(word, end='', flush=True)
        self.bot_msg = self.bot_msg + word

    def new_dialog(self):
        self.bot.new_chat()
        clear_console()
        print('User clear,stack was cleared. New chat will begin.')
        greet()

    def chat(self, msg):
        msg = msg.strip()
        print(Fore.CYAN + self.bot_name + ': ', end='')
        self.bot.chat(msg)
        # self.util.chat(msg, context=self.msg_stack)
        print(Style.RESET_ALL)

    def loop(self):
        self.bot_msg = ''
        print(Fore.LIGHTGREEN_EX + self.user_name + ': ', end='')
        msg = input()
        print(Style.RESET_ALL, end='')
        if not msg:
            return
        if is_quit(msg):
            self.running = False
            return
        if os.path.exists(msg):
            msg = f'file:{msg}'
        ai, dialog = process_ai_message(msg)
        if ai:
            out_ai_role_msg(self.fm_name, self.system_name, msg, dialog)
        else:
            self.chat(msg)
            try:
                term_width = int(os.get_terminal_size().columns / 3)
            except:
                term_width = 100
            tips_out(' - ' * term_width)
