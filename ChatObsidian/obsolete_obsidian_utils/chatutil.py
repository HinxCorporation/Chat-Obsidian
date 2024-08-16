import configparser
import logging
import time

from ..InsChatBot import *


class ChatUtil:

    def __init__(self):
        # Configure logging
        logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')
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

        self.bot = InsChatBot(self.get_color, 'AI')

    def get_color(self, colorName):
        exist = self.colors.__contains__(colorName)
        if exist:
            color = self.colors[colorName]
        else:
            color = None
        return exist, color

    def chat(self, msg, context=None, max_tk=2048, model=''):
        # context is the obsidian message chain , needs to complete it as new chat.
        self.bot.current_chat = Chat()
        self.bot.current_chat.messages.extend(context)
        self.bot.chat(msg)

    def complete_obsidian_chat(self, canvas_file, wdir):
        """
        scan that file and make transitions
        """

        # Needs to block if file continues edit

        with open(canvas_file, 'r', encoding='utf-8') as f:
            json_dat = json.load(f)
            nodes = json_dat['nodes']
            edges = json_dat['edges']

        ids = set()
        for e in edges:
            ids.add(e['fromNode'])

        # find all none point chat node , then make handle.
        goes_to_chat = [n for n in nodes if validate_chat_node(n, ids)]
        i_len = len(goes_to_chat)
        if i_len > 0:
            print(f'new chat: {i_len}')
            for blank_node in goes_to_chat:
                self.bot.complete_obsidian_chat(blank_node['id'], canvas_file, nodes, edges, wdir)
                # current.current_chat, text = process_relative_block(util, nodes, edges, blank_node, file, note_root)
                # print(f 'begin chat : {text} , update it to {current.current_chat}')
                # context = create_message_chain(blank_node, nodes, edges, note_root)
                # # print(context)
                # print_context(context)
                # util.chat(text, context)
                time.sleep(2)
        else:
            pass
