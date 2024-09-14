from PyAissistant import ChatBot, DeepSeekBot

from ChatObsidian import run_obsidian


def list_all_functions():
    # list_all_functions()
    bot: ChatBot = DeepSeekBot()
    bot.chat('Hi bot, list all functions please.')


if __name__ == '__main__':
    run_obsidian()
