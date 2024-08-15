import configparser
import logging

import requests

from .chat_api import ChatBot_obs
from .chat_bot_util import *


class DeepSeekBot_obs(ChatBot_obs):
    """
    the obsolete version of DeepSeekBot
    """

    def __init__(self, post_words=print_words):
        super().__init__(post_words)
        config_file = 'config.ini'
        config = configparser.ConfigParser()
        try:
            config.read(config_file, encoding='utf-8')
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

    def create_request(self, **kwargs):
        if self.use_proxy:
            return requests.request("POST", self.url, stream=True, proxies={"https": self.proxy_uri, }, **kwargs)
        else:
            return requests.request("POST", self.url, stream=True, proxies={"http": "", "https": ""}, **kwargs)

    def go_next(self, content: str):
        # find the first block
        position = content.find(self.block_mark)
        if position != -1:
            current_line = content[:position].strip()
            rest_content = content[position + len(self.block_mark):]
            return current_line, rest_content
        return '', content

    def try_outline(self, input_str):
        line, input_str = self.go_next(input_str)
        if line:
            word = get_words_deep_seek_bot(line)
            # print(f'{word}: in {line}')
            self._write_out(word), word
        return input_str, ""

    def get_color(self, colorName):
        exist = self.colors.__contains__(colorName)
        if exist:
            color = self.colors[colorName]
        else:
            color = None
        return exist, color

    def _generate_response(self, user_input: str) -> [str, str]:
        # response = self.client.request_completion(model="llama3.1", stream=True, prompt=message)
        chain = self.message_chain()
        model = self.model
        payload = json.dumps({
            "messages": chain,
            "model": model,
            "frequency_penalty": 0,
            "max_tokens": 2048,
            "presence_penalty": 0,
            "stop": None,
            "stream": True,
            "temperature": 1,
            "top_p": 1,
            "logprobs": False,
            "top_logprobs": None
        })
        with open('payload.json', 'w', encoding='utf-8') as f:
            f.write(payload)
        response_text = ""
        msg_stack = ""
        try:
            response = self.create_request(headers=self.headers, data=payload)
            response.raise_for_status()
            with open('response.dat', 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
                    chunk_text = chunk.decode('utf-8')  # Decode bytes to string
                    msg_stack += chunk_text
                    # process every block
                    while msg_stack and self.block_mark in msg_stack:
                        msg_stack, w = self.try_outline(msg_stack)
                        response_text += w
        except requests.exceptions.RequestException as e:
            print(e)
            logging.error(f"Request error: {e}")
        except Exception as e:
            print(e)
            logging.error(f"Error: {e}")

        # from message stack line 0 read id
        try:
            first_line = msg_stack.splitlines()[0][len(self.block_mark)+1:]
            json_data = json.loads(first_line)
            uuid_tex = json_data.get('id')
        except:
            uuid_tex = generate_uuid(32)

        return response_text, uuid_tex
