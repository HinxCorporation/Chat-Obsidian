import os

from PyAissistant import ChatBot, DeepSeekBot

from ChatObsidian import run_obsidian
from obsidian_flow import run as run_flow


def list_all_functions():
    # list_all_functions()
    bot: ChatBot = DeepSeekBot()
    bot.chat('Hi bot, list all functions please.')


if __name__ == '__main__':
    # if debug
    if os.getenv('DEBUG') == 'True':
        run_obsidian()
    else:
        run_flow()
