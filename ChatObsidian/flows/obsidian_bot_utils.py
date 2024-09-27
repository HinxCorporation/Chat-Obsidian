import configparser
import inspect
import json
import os

import yaml
from PyAissistant import DeepSeekBot as ChatBot

from ..InsChatBot import OpenAIBot as DeepSeekOpenAI, OllamaBot as OllamaBot, RestBot as DeepSeekBot

__all__ = ['construct_bot', 'bot_set_instance']


def _print_with_color(color, text):
    text = text.strip()
    if not text.startswith('\t'):
        text = '\t' + text
    print(f'\033[3{color}m{text} \033[0m')


def red_print(text):
    _print_with_color(1, text)


def green_print(text):
    _print_with_color(2, text)


def yellow_print(text):
    _print_with_color(3, text)


def blue_print(text):
    _print_with_color(4, text)


def purple_print(text):
    _print_with_color(5, text)


def alice_print(text):
    _print_with_color(6, text)


class _BotSetUpInstance:
    def __init__(self):
        self.builtin_bots = {}
        config_file = 'config.ini'
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file, encoding='utf-8')
        self.config = config
        self.colors = {}
        # load colors from config
        if self.config.has_section('Colors'):
            for key, value in self.config.items('Colors'):
                self.colors[key] = value
        purple_print(f'\tAlready load colors:{len(self.colors)}')
        self.program_args = {'get_color_method': self._get_color_fall_back,
                             'color_provider': self._get_color_fall_back}

        current = config.get('ai', 'current')

        if current:
            key = config.get(current, "key")
            url = config.get(current, "url")
            host = config.get(current, "host")
            model = config.get(current, "current")
            self.default_config = {
                'key': key,
                'url': url,
                'host': host,
                'model': model,
                'mode': 'rest'
            }
        else:
            self.default_config = {'prompt': 'Hello, how can I help you?', 'mode': 'OllamaBot'}

    def _get_color_fall_back(self, key):
        color = self.colors.get(key, None)
        if not color:
            return False, '#000'
        return True, color

    def _construct(self, mode, args):
        # mode:str is lower case
        extra_args = args.copy()
        if mode in ['deepseekbot', 'rest']:
            instance_class = DeepSeekBot
        elif mode in ['ollama', 'ollamabot']:
            instance_class = OllamaBot
        elif mode in ['openai', 'deepseekopenai']:
            dict_args = {}
            if self.config.has_section('DeepSeekBot'):
                dict_args.update(self.config.items('DeepSeekBot'))
            dict_args.update(extra_args)
            instance_class = DeepSeekOpenAI
            extra_args = dict_args
        else:
            red_print(f'Unsupported mode: {mode}')
            instance_class = ChatBot
        params = inspect.signature(instance_class.__init__).parameters
        filtered_args = {k: v for k, v in extra_args.items() if k in params}
        # remove used args on config
        for key in filtered_args:
            args.pop(key, None)
        return instance_class(**filtered_args)

    @staticmethod
    def test_match(bot, hints):
        # get name or __name__ from bot
        bot_name = getattr(bot, '__name__', None)
        if bot_name:
            # hints maybe name or starts with name:
            if bot_name in hints or hints.startswith(bot_name + ':'):
                return True
        return False

    def create_bot_from_config(self, config: dict, hints):
        mode = config.get('mode', 'openai')
        green_print(f' \tCreate Bot with: {mode}, Hint: {hints}')

        # coping args from program
        for key, value in self.program_args.items():
            if not config.get(key, None):
                config[key] = value
        # remove mode from config
        config.pop('mode')
        if 'title' not in config:
            if 'name' in config:
                config['title'] = config['name']
            else:
                if len(hints) < 10:
                    config['title'] = hints
                else:
                    config['title'] = hints[:8] + '❤'
        # ensure title is first char upper case
        config['title'] = config['title'][0].upper() + config['title'][1:]
        try:
            bot = self._construct(mode.strip().lower(), config)
        except Exception as e:
            red_print(f'Failed to create bot with mode: {mode}, Hint: {hints}, Error: {e}')
            bot = None
        if bot is not None:
            # green_print(f'Completed args setup, Now sync args with custom inputs')
            for key, value in config.items():
                if hasattr(bot, key):
                    try:
                        # blue_print(f' \tUpdate bot with: {key}')
                        setattr(bot, key, value)
                    except:
                        red_print(f' \tSET:{key} Failure on bot:{hints}')
                        pass
                else:
                    pass
        else:
            red_print(f'Failed to create bot with mode: {mode}, Hint: {hints}')
        return bot

    def select_chat_bot(self, hints):
        for bot in self.builtin_bots:
            if self.test_match(bot, hints):
                return bot
        return None

    def instance_chat_bot(self, hints, **kwargs):
        """
        Instance a chat bot from hints, hints may a tag or point to a bot config file
        """
        try:
            bot = self.select_chat_bot(hints)
            if bot:
                return bot
            cd = kwargs.get('cd', None)
            if not cd:
                cd = kwargs.get('current_dir', None)
            if not cd:
                cd = os.getcwd() + '/bots'
            bot_profile = os.path.abspath(os.path.join(cd, hints)).replace('\\', '/')

            # alice_print(f' \tTry load bot profile from: {bot_profile}')
            config_file = bot_profile
            if os.path.isdir(bot_profile):
                config_file = os.path.join(bot_profile, 'config.yaml').replace('\\', '/')
            # ensure ends with .json or .yaml or ini
            if not config_file.endswith(('.json', '.yml', '.yaml', '.ini', '.txt')):
                # if +.json exists
                if os.path.exists(config_file + '.json'):
                    config_file += '.json'
                # if +.yml exists
                elif os.path.exists(config_file + '.yml'):
                    config_file += '.yml'
                # if +.yaml exists
                elif os.path.exists(config_file + '.yaml'):
                    config_file += '.yaml'
                # if +.ini exists
                elif os.path.exists(config_file + '.ini'):
                    config_file += '.ini'
                elif os.path.exists(config_file + '.txt'):
                    config_file += '.txt'
                else:
                    pass

            _, bot = self.instance_chat_bot_from_file(config_file, **kwargs)
            return bot
        except:
            # raise e
            pass
        return None

    def _from_file_load_configs(self, file_path):
        """
                load file as bot create config
        """
        # support json, yaml, ini , txt
        config_type = os.path.splitext(file_path)[1]
        if config_type == '.json':
            config = json.load(open(file_path, 'r', encoding='utf-8'))
        elif config_type == '.yaml' or config_type == '.yml':
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        elif config_type == '.ini':
            config = configparser.ConfigParser()
            config.read(file_path, encoding='utf-8')
        elif config_type == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                config = self.default_config.copy()
                _prompt_text = f.read()
                if _prompt_text:
                    # add or update prompt
                    _prompt_text = _prompt_text.strip()
                    if _prompt_text.startswith('prompt:'):
                        _prompt_text = _prompt_text[7:].strip()
                    # update config dict
                    config['prompt'] = _prompt_text
        else:
            config = None
        return config

    def instance_chat_bot_from_file(self, file_path, **kwargs):
        if os.path.exists(file_path):
            config = self._from_file_load_configs(file_path)
            if config:
                name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
                bot = self.create_bot_from_config(config, name_without_extension)
                if bot is not None:
                    # try update attributes from kwargs
                    for key, value in kwargs.items():
                        if hasattr(bot, key):
                            try:
                                setattr(bot, key, value)
                            except:
                                # ignore error
                                pass
                else:
                    red_print(f'Failed to create bot from config: {file_path}')
                return bot is not None, bot
            else:
                red_print(f'Failed to load config from file: {file_path}')
        else:
            red_print(f'File not exists: {file_path}')
        return False, None


bot_set_instance = None


def get_instance():
    global bot_set_instance
    if not bot_set_instance:
        bot_set_instance = _BotSetUpInstance()
    return bot_set_instance


def construct_bot(hints, **kwargs) -> (bool, ChatBot):
    # host = kwargs.get('program', None)
    # if host is _process_messages_step, host.data and host.monitor
    args = kwargs.copy()
    # exclude program if exists
    if 'program' in args:
        del args['program']
    instance = get_instance()
    if instance:
        if hints.startswith('file:'):
            file_path = hints[5:].strip()
            if os.path.isfile(file_path):
                # with open(file_path, 'r', encoding='utf-8') as f:
                #     hints = f.read()
                return instance.instance_chat_bot_from_file(file_path, **args)
            else:
                return False, None
        bot = instance.instance_chat_bot(hints, **args)
        if bot:
            # green_print(f' \tBot created for {hints}')
            return True, bot
        else:
            red_print(f'Failed to create bot for {hints}')
        return False, None
    return False, None
