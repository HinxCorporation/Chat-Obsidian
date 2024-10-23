import os

import requests
from PyAissistant import DeepSeekOpenAI

from ChatObsidian import OpenAIBot
from .text_file_writer import TextFileWriter


class WebPageManager:

    def __init__(self, bot, host, custom_folder="temp/knowledge_base/terraria_wiki_gg/"):
        self.bot = bot
        if host.endswith('/'):
            host = host[:-1]
        self.host = host
        self.folder = custom_folder
        self.system_prompt = """
    You are a document optimizer, Your job is to make document human-readable and easy to understand.
    The document should output with users requirements. and `[finished]` with complete.Because of the system limit, The
    document should be less than 8000 tokens and may not complete yet, while user request for continue 
    then continue the task. Continue is not restart the task, it is continue the task,remember that.

    for example:
    user: make this doc as markdown format : long text ...
    bot: 
    # Title 
    ## Subtitle 
    content...
    [finished]

    The document should be easy to read and understand for users. If the document is complete , 
    it should end with `[finished]`.
    """
        self.current_file = ''
        self.is_complete = False
        self.text_buffer = ''
        self.writer: TextFileWriter
        self.writer = None
        self.print_console = False

    @staticmethod
    def read_web_page(url):
        """
        read a web page and return its content, url should start with "http://" or "https://"
        :param url: the url of the web page
        :return: the content of the web page
        """
        try:
            if url.startswith('http://') or url.startswith('https://'):
                pass
            else:
                url = 'http://' + url
            if url.endswith('/'):
                url = url[:-1]
            print(f'Read web page: {url} ...')
            rr = requests.get(url, proxies={"http": None, "https": None})
            if rr.status_code != 200:
                print('Failed to read web page, code:' + str(rr.status_code))
                return False, 'Failed to read web page, code:' + str(rr.status_code)
            return True, rr.text
        except Exception as e:
            return False, str(e)

    def write_file(self, content):
        if not content:
            return
        if self.print_console:
            print(content, end='')
            return
        self.writer.write(content)
        self.text_buffer += content

        if len(self.text_buffer) > 30:
            last_30 = self.text_buffer[-30:].lower()
            if '[finished]' in last_30:
                self.is_complete = True
                print('Document is complete ' + last_30)

    def get_article_file(self, title):
        _file = os.path.join(self.folder, title).replace("\\", "/")
        _file = os.path.abspath(_file)
        folder, _ = os.path.split(_file)
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        return _file

    def setup_save_file(self, file_name):
        self.current_file = self.get_article_file(file_name)
        self.writer = TextFileWriter(self.current_file, True, debug_console=True)
        print(f'Text writer setup complete, file: {self.current_file} ...')

    def do_process_page(self, title, processor=None, custom_prompt=None,
                        continue_message='not finished yet, pls continue', special_file=None):
        if not special_file:
            special_file = title.replace(' ', '_') + '.md'
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            special_file = special_file.replace(char, '')

        url = f'{self.host}/{title}'
        if url.endswith('/'):
            url = url[:-1]
        su, content = self.read_web_page(url)
        if not su:
            print(f'Failed to read web page: {url}')
            print(content)
        else:
            processor(content, special_file, custom_prompt, continue_message)
            pass

    def process_page_as(self, content, special_file=None, user_prompt=None,
                        continue_message='not finished yet, pls continue'):
        print(f'Read web complete, start processing ...')
        self.setup_save_file(special_file)
        self.bot.new_chat()
        bot = self.bot
        bot._write_out = self.write_file
        bot.current_chat.system_prompt = self.system_prompt
        # bot.stream = False
        if bot.executor is not None:
            bot.executor.clear_tools()
        self.is_complete = False
        # user_prompt = (f"Please help me optimize the document, make it Human-readable and easy to understand."
        #                f"make them knowledge and out with markdown format.\n{content}")
        user_prompt = f'{user_prompt}\n{content}'
        try:
            bot.chat(user_prompt)
            while not self.is_complete:
                bot.chat(continue_message)
            print('[Done]')
            self.writer.close()
        # user key interrupt
        except KeyboardInterrupt:
            print('User interrupt, exit ...')
            self.writer.close()
        except Exception as e:
            print(f'Error occurred: {str(e)}')
            self.writer.close()

    def process_page(self, title, special_file=None):
        user_prompt = (f"Please help me optimize the document, make it Human-readable and easy to understand."
                       f"make them knowledge and out with markdown format.")
        self.do_process_page(title, processor=self.process_page_as, custom_prompt=user_prompt,
                             special_file=special_file)

    def read_article(self, article, special_file=None):
        preserved_file = self.get_article_file(article)
        if not os.path.exists(preserved_file):
            self.process_page(article, preserved_file)
        with open(preserved_file, "r", encoding="utf-8") as f:
            return f.read()

    def ask_around_pages(self, articles, question) -> None:
        knowledges = [self.read_article(article) for article in articles]
        self.bot.new_chat()
        pass


def demo():
    os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    bot = DeepSeekOpenAI()
    host = 'https://terraria.wiki.gg/wiki/'
    mgr = WebPageManager(bot, host)
    # mgr.process_page('Terraria_Wiki')
    mgr.process_page('List_of_weapons')


class TerrKnowledgeAssist(OpenAIBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.working_dir = "terra_knowledge_assist"
        self.host = 'https://terraria.wiki.gg/'

    def setup_function_tools(self):
        self.executor.add_tool(self.write_file)
        self.executor.add_tool(self.read_web_page)

    def _get_full_name(self, file_name):
        combined_name = self.working_dir + "/" + file_name
        full_name = os.path.abspath(combined_name).replace("\\", "/")
        folder, name = os.path.split(full_name)
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        return full_name

    def write_file(self, file_name, content):
        """
        write a text file, for example a doc of terraria knowledge with md format
        :param file_name: the name of the file, including the extension, able to use relative path for
          example: "items/desc.md"
        :param content: the content of the file
        :return: a message indicating whether the write operation is successful or not
        """
        try:
            file_name = self._get_full_name(file_name)
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(content)
            return 'write successful'
        except Exception as e:
            return 'write failed:' + str(e)

    @staticmethod
    def read_web_page(url):
        """
        read a web page and return its content, url should start with "http://" or "https://"
        :param url: the url of the web page
        :return: the content of the web page
        """
        response = requests.get(url)
        if response.status_code != 200:
            return 'Failed to read web page, code:' + str(response.status_code)
        return response.text
