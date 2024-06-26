import configparser
import json
import logging
import os
import re

import requests


class ChatUtil:

    def __init__(self, c_out):
        # Configure logging
        logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')
        self.cout = c_out
        config_file = 'config.ini'
        config = configparser.ConfigParser()

        try:
            config.read(config_file,encoding='utf-8')
            current = config.get('ai', 'current')
            self.key = config.get(current, "key")
            self.url = config.get(current, "url")
            self.model = config.get(current, "current")
            self.cache_transitions = config.getboolean("setting", "cache_transitions", fallback=False)
            self.use_proxy = config.getboolean("setting", "use_proxy", fallback=False)
            self.proxy_uri = config.get("setting", "proxy", fallback='')
            print('AI:', current, self.url)
            if self.use_proxy:
                print('using Proxy:', self.proxy_uri)

            color_block_options = config.options('Colors')
            self.colors = dict()
            for key in color_block_options:
                self.colors[key] = config.get('Colors', key)

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logging.error(f"Error reading config file: {e}")
            raise

        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.key}'
        }
        self.block_mark = 'data:'

    def get_color(self, colorName):
        exist = self.colors.__contains__(colorName)
        if exist:
            color = self.colors[colorName]
        else:
            color = None
        return exist, color

    def create_request(self, **kwargs):
        if self.use_proxy:
            return requests.request("POST", self.url, stream=True, proxies={"https": self.proxy_uri, }, **kwargs)
        else:
            return requests.request("POST", self.url, stream=True, proxies={"http": "", "https": ""}, **kwargs)

    def go_next(self, content: str):
        position = content.find(self.block_mark)
        if position != -1:
            current_line = content[:position].strip()
            rest_content = content[position + len(self.block_mark):].strip()
            return current_line, rest_content
        return '', content.strip()

    @staticmethod
    def parse_to_filename(input_string: str, length=12):
        """
        Parse the input string and convert it to a valid filename.

        Args:
            input_string (str): The input string to be parsed.
            length (int): The maximum length of the output filename. Default is 12.

        Returns:
            str: The parsed and valid filename.
        """
        INVALID_CHARS_FOR_FILENAMES = re.compile(r'[<>:"/\\|?*]')
        REPLACED_CHARS = ['\n', '\r', '\t', '#', '%', '&', '^', '@', '~', '!', '$']
        if len(input_string) > length:
            input_string = input_string[:length]
        for char in REPLACED_CHARS:
            input_string = input_string.replace(char, '')
        valid_filename = INVALID_CHARS_FOR_FILENAMES.sub('', input_string).strip()
        return valid_filename[:length] + '...' if len(valid_filename) > length else valid_filename

    def try_outline(self, input_str):
        line, input_str = self.go_next(input_str)
        if line:
            self.cout(line)
        return input_str

    def chat(self, msg, context=None, max_tk=2048, model=''):
        if not model:
            model = self.model
        if not context:
            context = [
                {
                    "content": "You are a helpful assistant",
                    "role": "system"
                }
            ]
        context = [*context,
                   {
                       "content": msg,
                       "role": "user"
                   }]

        msg_stack = ''
        payload = json.dumps({
            "messages": context,
            "model": model,
            "frequency_penalty": 0,
            "max_tokens": max_tk,
            "presence_penalty": 0,
            "stop": None,
            "stream": True,
            "temperature": 1,
            "top_p": 1,
            "logprobs": False,
            "top_logprobs": None
        })
        try:
            response = self.create_request(headers=self.headers, data=payload)
            response.raise_for_status()

            cache = None
            if self.cache_transitions:
                cache_name = self.parse_to_filename(msg) + '.response.json'
                if not os.path.exists('caches'):
                    os.mkdir('caches')
                cache = open('caches/' + cache_name, 'w', encoding='utf-8')

            for chunk in response.iter_content(chunk_size=1024):
                chunk = chunk.decode('utf-8')  # Decode bytes to string
                if cache:
                    cache.write(chunk)
                msg_stack += chunk
                msg_stack = self.try_outline(msg_stack)
            if cache:
                cache.close()
            while msg_stack and self.block_mark in msg_stack:
                msg_stack = self.try_outline(msg_stack)
        except requests.exceptions.RequestException as e:
            print(e)
            logging.error(f"Request error: {e}")
        except Exception as e:
            print(e)
            logging.error(f"Error: {e}")
