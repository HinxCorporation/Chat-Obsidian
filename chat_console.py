from PyAissistant import ChatBot, DeepSeekBot


from ChatObsidian import chat_console


def list_all_functions():
    # list_all_functions()
    bot: ChatBot = DeepSeekBot()
    bot.chat('Hi bot, list all functions please.')


if __name__ == '__main__':
    try:
        chat_console.run()
    except KeyboardInterrupt:
        print('Exiting...')


