import configparser
import json
import logging

import requests


class ChatUtil:
    """
    o llama chat bot
    """

    def __init__(self, c_out):
        # Configure logging
        logging.basicConfig(filename='errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')
        self.cout = c_out
        config_file = 'config.ini'
        config = configparser.ConfigParser()

        try:
            config.read(config_file, encoding='utf-8')
            current = config.get('ai', 'current')
            # curl
            # http: // localhost: 11434 / api / generate - d
            # '{
            # > "model": "llama3",
            # > "prompt": "介绍一下你自己?"
            # >}'

            self.api = 'api/generate'
            self.url = "http://localhost:11434/" + self.api
            color_block_options = config.options('Colors')
            self.colors = dict()
            for key in color_block_options:
                self.colors[key] = config.get('Colors', key)

        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            logging.error(f"Error reading config file: {e}")
            raise

        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def get_color(self, colorName):
        exist = self.colors.__contains__(colorName)
        if exist:
            color = self.colors[colorName]
        else:
            color = None
        return exist, color

    def create_request(self, **kwargs):
        return requests.request("POST", self.url, stream=True, proxies={"http": "", "https": ""}, **kwargs)

    @staticmethod
    def go_next(content: str):
        lines = content.splitlines()
        if not lines:
            return "", ""
        if len(lines) > 1:
            return lines[0].strip(), "\n".join(lines[1:]).strip()
        return "", content.strip()

    def try_outline(self, input_str):
        line, input_str = self.go_next(input_str)
        if line:
            self.cout(line)
        return input_str

    def chat(self, msg, context=None):
        # if not context:
        #     context = [
        #         {
        #             "content": "You are a helpful assistant",
        #             "role": "system"
        #         }
        #     ]
        # context = [*context,
        #            {
        #                "content": msg,
        #                "role": "user"
        #            }]

        msg_stack = ''
        # '{
        # > "model": "llama3",
        # > "prompt": "介绍一下你自己?"
        # >}'
        payload = json.dumps({
            "model": 'llama3',
            "prompt": msg,
        })
        try:
            response = self.create_request(headers=self.headers, data=payload)
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=1024):
                chunk = chunk.decode('utf-8')  # Decode bytes to string
                msg_stack += chunk
                msg_stack = self.try_outline(msg_stack)
            while msg_stack and '\n' in msg_stack:
                msg_stack = self.try_outline(msg_stack)
        except requests.exceptions.RequestException as e:
            print(e)
            logging.error(f"Request error: {e}")
        except Exception as e:
            print(e)
            logging.error(f"Error: {e}")
