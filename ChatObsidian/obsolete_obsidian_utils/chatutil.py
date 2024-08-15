import configparser
import logging

from PyAissistant.PyChatBot.chat_api import ChatBot
from PyAissistant.PyChatBot.deep_seek_bot import DeepSeekBot


class ChatUtil:

    def __init__(self, c_out):
        # Configure logging
        logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')
        self.cout = c_out
        config_file = 'config.ini'
        config = configparser.ConfigParser()

        try:
            config.read(config_file, encoding='utf-8')
            color_block_options = config.options('Colors')
            self.colors = dict()
            for key in color_block_options:
                self.colors[key] = config.get('Colors', key)

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logging.error(f"Error reading config file: {e}")
            raise

        bot: ChatBot = DeepSeekBot(post_words=c_out)
        self.bot = bot

    def get_color(self, colorName):
        exist = self.colors.__contains__(colorName)
        if exist:
            color = self.colors[colorName]
        else:
            color = None
        return exist, color

    def chat(self, msg, context=None, max_tk=2048, model=''):
        self.bot.chat(msg)
