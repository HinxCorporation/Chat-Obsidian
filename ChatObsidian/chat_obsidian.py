# listen to a canvas file , and make sure all content has response.

import configparser
import datetime
import json
import logging
import os
import threading

import colorlog

from .InsChatBot import InsChatBotGeneric as InsChatBot, InsBot
from .WatcherUtil import initialize_config, setup_observers, run_observers
from .obsolete_obsidian_utils.obsidian_utils import validate_chat_node


# from .obsolete_obsidian_utils import ChatUtil


def run():
    success, note_root, folders_list = initialize_config()
    if not success:
        return

    try:
        util = ChatUtil()
        # util.cache_transitions = True
    except Exception as e:
        print('initialize failure. pls check your config file.')
        # raise e
        print(e)
        raise e

    observers = setup_observers(note_root, folders_list)
    # print a green color message to indicate the program is running.
    print('\033[92m' + 'ChatObsidian is running...\nConsole Gonna stop, ctrl + c to exit\n' + '\033[0m')
    run_observers(observers, util=util, note_root=note_root)
    print('program quit.')


def load_blank_nodes_from_canvas_file(canvas_file: str):
    nodes = []
    edges = []
    if not os.path.exists(canvas_file):
        return [], nodes, edges
    try:
        with open(canvas_file, 'r', encoding='utf-8') as f:
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
    blank_nodes = [n for n in nodes if validate_chat_node(n, ids)]
    return blank_nodes, nodes, edges


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
            fmt = logging.Formatter(
                fmt="[%(asctime)s.%(msecs)03d] %(filename)s:%(lineno)d [%(levelname)s]: %(message)s",
                datefmt='%Y-%m-%d  %H:%M:%S')

            sh_fmt = colorlog.ColoredFormatter(
                fmt="%(log_color)s[%(asctime)s.%(msecs)03d]-[%(levelname)s]: %(message)s",
                datefmt='%Y-%m-%d  %H:%M:%S',
                log_colors=log_colors_config)
            # 给处理器添加格式
            sh.setFormatter(fmt=sh_fmt)
            fh.setFormatter(fmt=fmt)
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
    colors = None

    @staticmethod
    def _get_colors():
        if ChatUtil.colors is None:
            config = configparser.ConfigParser()
            config_file = 'config.ini'
            try:
                config.read(config_file, encoding='utf-8')
                color_block_options = config.options('Colors')
                ChatUtil.colors = dict()
                for key in color_block_options:
                    ChatUtil.colors[key] = config.get('Colors', key)
            except:
                pass
        return ChatUtil.colors

    @staticmethod
    def get_color_static(colorName):
        colors = ChatUtil._get_colors()
        exist = colors.__contains__(colorName)
        if exist:
            color = colors[colorName]
        else:
            color = None
        return exist, color

    @staticmethod
    def __CREATE_BOT__(get_color_method=None) -> InsChatBot:
        if get_color_method is None:
            get_color_method = ChatUtil.get_color_static
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
            # print('\033[32m' + f"Bot {botName} created with prompt: {prompt}" + '\033[0m')
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
        self.advanced = True

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
        goes_to_chat, nodes, edges = load_blank_nodes_from_canvas_file(canvas_file)
        i_len = len(goes_to_chat)
        if i_len > 0:
            for blank_node in goes_to_chat:
                if self.advanced:
                    args = {'color_provider': self.get_color}
                    bot = InsBot(args)
                    print('using advanced mode')
                    threading.Thread(target=lambda: bot.processing(node_id=blank_node['id'],
                                                                   canvas_file=canvas_file,
                                                                   root_dir=wdir,
                                                                   nodes=nodes,
                                                                   edges=edges)).start()
                else:
                    bot = ChatUtil.__CREATE_BOT__(self.get_color)
                    threading.Thread(target=lambda: bot.complete_obsidian_chat(blank_node['id'], canvas_file, nodes,
                                                                               edges, wdir)).start()
        else:
            pass
