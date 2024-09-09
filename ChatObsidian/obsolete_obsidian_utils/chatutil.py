import configparser
import datetime
import json
import logging
import os
import threading

import colorlog

from .obsidian_utils import validate_chat_node
from ..InsChatBot import InsChatBot


class ObsidianBotInstance:
    util = None
    functions: list = []
    log_dir = "bot_logs"
    logger = None

    @staticmethod
    def __set_up_logger__():
        log_dir = os.path.join(os.getcwd(), ObsidianBotInstance.log_dir)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_colors_config = {
            'DEBUG': 'white',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
        # create a special ai bot logger
        logger = logging.getLogger('Obsidian AI Bot')
        logger.setLevel(20)
        now = datetime.datetime.now()
        file_name = now.strftime('%Y%m%d_%H%M%S') + ".log"
        log_path = os.path.join(log_dir, file_name)

        # create log folder if it is not exist.
        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)

        if not logger.handlers:  # 作用,防止重新生成处理器
            sh = logging.StreamHandler()  # 创建控制台日志处理器
            fh = logging.FileHandler(filename=log_path, mode='a', encoding="utf-8")  # 创建日志文件处理器
            # 创建格式器
            # fmt = logging.Formatter(
            #     fmt="[%(asctime)s.%(msecs)03d] %(filename)s:%(lineno)d [%(levelname)s]: %(message)s",
            #     datefmt='%Y-%m-%d  %H:%M:%S')

            sh_fmt = colorlog.ColoredFormatter(
                fmt="%(log_color)s[%(asctime)s.%(msecs)03d]-[%(levelname)s]: %(message)s",
                datefmt='%Y-%m-%d  %H:%M:%S',
                log_colors=log_colors_config)
            # 给处理器添加格式
            sh.setFormatter(fmt=sh_fmt)
            fh.setFormatter(fmt=sh_fmt)
            # 给日志器添加处理器，过滤器一般在工作中用的比较少，如果需要精确过滤，可以使用过滤器
            logger.addHandler(sh)
            logger.addHandler(fh)
            # print out green color to indicate logger is set up successfully
            print('\033[32m' + "Logger set up successfully" + '\033[0m')
        else:
            # print out orange color to indicate logger is already set up
            print('\033[33m' + "Logger already set up, skipping" + '\033[0m')

        ObsidianBotInstance.logger = logger
        ObsidianBotInstance.log_dir = log_dir

    @staticmethod
    def set_up():
        ObsidianBotInstance.__set_up_logger__()
        for attr in dir(ObsidianBotInstance):
            if callable(getattr(ObsidianBotInstance, attr)) and not attr.startswith("__"):
                # exclude set_up and __init__
                if attr == "set_up" or attr == "__init__":
                    continue
                ObsidianBotInstance.functions.append(getattr(ObsidianBotInstance, attr))
        msg = f"Obsidian Bot Instance set up complete : {datetime.datetime.now()}"
        # print out msg with color
        print('\033[32m' + msg + '\033[0m')
        ObsidianBotInstance.logger.info(msg)
        pass

    @staticmethod
    def read_log_file(log_file_name):
        """
        read a log file under the log directory, return the content as string
        log was write by AI bot self, free and easy to access
        :param log_file_name: log file name under the log directory
        """
        try:
            full_path = os.path.join(ObsidianBotInstance.log_dir, log_file_name)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "log file not found under the log directory"
        except Exception as e:
            return f"Error reading log file (maybe some one else is using this file) : {e}"

    @staticmethod
    def write_log(message):
        """ write a message to log file under the log directory """
        ObsidianBotInstance.logger.info(message)
        return "success"

    @staticmethod
    def write_error_log(message):
        """ write an error message to log file under the log directory """
        ObsidianBotInstance.logger.error(message)
        return "success"

    @staticmethod
    def write_warning_log(message):
        """ write a warning message to log file under the log directory """
        ObsidianBotInstance.logger.warning(message)
        return "success"

    @staticmethod
    def list_log_files():
        """ list all log files under the log directory """
        return "\n".join(os.listdir(ObsidianBotInstance.log_dir))


class ChatUtil:

    @staticmethod
    def __CREATE_BOT__(get_color_method):
        bot = InsChatBot(get_color_method, 'AI')
        bot_config_file = 'bot_config.ini'
        try:
            # create config file if not exist
            if not os.path.exists(bot_config_file):
                with open(bot_config_file, 'w', encoding='utf-8') as f:
                    f.write('[Bot]\n')
                    f.write('name=AI\n')
                    f.write('model_path=deepseek-chat,deepseek-coder\n')
                    f.write('temperature=0.7\n')
                    f.write('top_p=0.9\n')
                    f.write('max_length=2048\n')
                    f.write('no_sample=False\n')
                    f.write('seed=42\n')
                    f.write('nsamples=1\n')
                    f.write('batch_size=1\n')
                    f.write('length=20\n')
                    f.write('prompt=')
            bot_config = configparser.ConfigParser()
            bot_config.read(bot_config_file, encoding='utf-8')
            botName = bot_config.get('Bot', 'name')
            model_path = bot_config.get('Bot', 'model_path')
            temperature = bot_config.getfloat('Bot', 'temperature')
            top_p = bot_config.getfloat('Bot', 'top_p')
            max_length = bot_config.getint('Bot', 'max_length')
            prompt = bot_config.get('Bot', 'prompt')

            if prompt:
                if prompt.startswith('file:'):
                    prompt = prompt[5:]
                if os.path.exists(prompt):
                    with open(prompt, 'r', encoding='utf-8') as f:
                        prompt = f.read()
            bot.set_config(botName, model_path, temperature, top_p, max_length, prompt)
        except:
            logging.error(f"Error reading bot config file: {bot_config_file}")
            raise
        bot.append_tool_call_result = False
        bot.executor.extend(ObsidianBotInstance.functions)
        return bot

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
        ObsidianBotInstance.util = self
        ObsidianBotInstance.set_up()

    def get_color(self, colorName):
        exist = self.colors.__contains__(colorName)
        if exist:
            color = self.colors[colorName]
        else:
            color = None
        return exist, color

    def complete_obsidian_chat(self, canvas_file, wdir):
        """
        scan that file and make transitions
        """
        # Needs to block if file continues edit
        nodes = []
        edges = []
        with open(canvas_file, 'r', encoding='utf-8') as f:
            try:
                json_dat = json.load(f)
                # maybe blank file in this case
                nodes = json_dat['nodes']
                edges = json_dat['edges']
            except:
                pass

        ids = set()
        for e in edges:
            ids.add(e['fromNode'])

        # find all none point chat node , then make handle.
        goes_to_chat = [n for n in nodes if validate_chat_node(n, ids)]
        i_len = len(goes_to_chat)
        if i_len > 0:
            for blank_node in goes_to_chat:
                bot = ChatUtil.__CREATE_BOT__(self.get_color)
                threading.Thread(target=lambda: bot.complete_obsidian_chat(blank_node['id'], canvas_file, nodes, edges,
                                                                           wdir)).start()
        else:
            pass
