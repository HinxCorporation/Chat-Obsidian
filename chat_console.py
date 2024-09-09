from PyAissistant.PyChatBot.chat_api import ChatBot
from PyAissistant.PyChatBot.deep_seek_bot import DeepSeekBot

from ChatObsidian import chat_console


def list_all_functions():
    # list_all_functions()
    bot: ChatBot = DeepSeekBot()
    bot.chat('Hi bot, list all functions please.')


if __name__ == '__main__':
    chat_console.run()


