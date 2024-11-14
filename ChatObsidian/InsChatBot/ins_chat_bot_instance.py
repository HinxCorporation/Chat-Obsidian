import json
import os

from PyAissistant import DeepSeekBot, DeepSeekOpenAI, OllamaBot

from .ins_chat_bot_custom import InsChatBotObsidianCustom


# Ins Shell needs bot should owns extra default_prompt , status, prompt :default_prompt "Ins: use of override build
# in prompt, used while chain do not provide prompt " :status "Ins: current status and running env for current bot"
# :prompt "Ins: use for input output prompt, may read from chain or read from file, or set by program; always used
#          if not none"


def save_messages(messages, bot_name):
    if not os.path.exists("temp"):
        os.makedirs("temp")
    with open(f"temp/{bot_name}_messages.json", "w") as f:
        f.write(json.dumps(messages, indent=4))


class OllamaChatBot(OllamaBot):
    def __init__(self,
                 color_provider,
                 file_title='-'):
        super().__init__()
        self.title = file_title
        self.color_provider = color_provider
        print('Instance of OllamaChatBot created')
        self._extend_prompt = ''
        self._default_prompt = None

    @property
    def system_prompt(self):
        if self.prompt:
            return f"{self.prompt}\n{super().system_prompt} "
        else:
            return super().system_prompt

    @property
    def default_prompt(self):
        return self._default_prompt

    @default_prompt.setter
    def default_prompt(self, value):
        self._default_prompt = value

    @property
    def prompt(self):
        return self._extend_prompt

    @prompt.setter
    def prompt(self, value):
        self._extend_prompt = value

    @property
    def status(self):
        return f"Ollama : {self.client.base_url}"

    def message_chain(self):
        msgs = super().message_chain()
        save_messages(msgs, "ollama")
        return msgs


class OpenAIChatBot(DeepSeekOpenAI):
    def __init__(self,
                 color_provider,
                 file_title='-',
                 write_out_call_result=None,
                 custom_append=None,
                 url=None,
                 host=None,
                 model=None,
                 key=None,
                 max_token=0,
                 temperature=0.7,
                 stream=False,
                 function_call_feat=True,
                 http_proxy="http://localhost:7890",
                 https_proxy="http://localhost:7890",
                 debug=False,
                 ):
        """
        :param color_provider: color provider for console output
        :param file_title: title of the file for saving messages
        :param write_out_call_result: function to write out the result of function call
        :param custom_append: custom append function call result
        :param url: url of openai api
        :param host: host of openai api
        :param model: model of openai api
        :param key: key of openai api
        :param max_token: max token of openai api
        :param temperature: temperature of openai api
        :param stream: stream of openai api
        :param function_call_feat: whether to use function call feature or not
        :param http_proxy: http proxy for openai api
        :param https_proxy: https proxy for openai api
        :param debug: debug mode for openai api
        """
        self.title = file_title
        self.color_provider = color_provider
        self.write_out_call_result = write_out_call_result
        self.custom_append = custom_append

        # must using proxy to access openai api
        os.environ['http_proxy'] = http_proxy
        os.environ['https_proxy'] = https_proxy
        super().__init__(None, function_call_feat,
                         custom_host=host,
                         custom_model=model,
                         custom_key=key,
                         custom_max_tokens=max_token,
                         custom_temperature=temperature,)
        if url is not None and url:
            self.url = url
        if max_token is not None and max_token > 10:
            self.max_token = max_token
        self.temperature = temperature
        if stream is not None:
            self.stream = stream
        self._extend_prompt = ''
        self._default_prompt = None
        self.debug = debug

    def execute_func(self, function_tool, **kwargs):
        tool_details = function_tool['function']
        function_name = tool_details['name']
        if self.custom_append is not None:
            # before calling function
            self.custom_append(f"\n> Working on `{function_name}` pls wait...")
        exec_result = super().execute_func(function_tool, **kwargs)
        self.write_out_call_result(function_name, kwargs, exec_result)
        return exec_result

    def message_chain(self):
        msgs = super().message_chain()
        save_messages(msgs, "openai")
        return msgs

    def _finish_openai_payload(self, messages):
        payloads = super()._finish_openai_payload(messages)
        if self.debug:
            print(f"payloads: {payloads}")
        return payloads

    @property
    def status(self):
        return f"OpenAI:host={self.host}, model={self.model}, key={self.key}"

    @property
    def default_prompt(self):
        return self._default_prompt

    @default_prompt.setter
    def default_prompt(self, value):
        self._default_prompt = value

    @property
    def system_prompt(self):
        if self.prompt:
            return f"{self.prompt}\n{super().system_prompt} "
        else:
            return super().system_prompt

    @property
    def prompt(self):
        return self._extend_prompt

    @prompt.setter
    def prompt(self, value):
        self._extend_prompt = value


class RestChatBot(DeepSeekBot):
    def __init__(self,
                 color_provider,
                 file_title='-',
                 write_out_call_result=None,
                 custom_append=None,
                 url=None,
                 host=None,
                 model=None,
                 key=None,
                 max_token=0,
                 temperature=0.7,
                 stream=True,
                 function_call_feat=True
                 ):
        super().__init__(None, function_call_feat)
        self.title = file_title
        self.color_provider = color_provider
        self.write_out_call_result = write_out_call_result
        self.custom_append = custom_append
        if url is not None and url:
            self.url = url
        if host is not None and host:
            self.host = host
        if model is not None and model:
            self.model = model
        if key is not None and key:
            self.key = key
        if max_token is not None and max_token > 10:
            self.max_token = max_token
        self.temperature = temperature
        if stream is not None:
            self.stream = stream
        self._default_prompt = None
        self._extend_prompt = ''

    def execute_func(self, function_tool, **kwargs):
        tool_details = function_tool['function']
        function_name = tool_details['name']
        if self.custom_append is not None:
            # before calling function
            self.custom_append(f"\n> Working on `{function_name}` pls wait...")
        exec_result = super().execute_func(function_tool, **kwargs)
        self.write_out_call_result(function_name, kwargs, exec_result)
        return exec_result

    def message_chain(self):
        msgs = super().message_chain()
        save_messages(msgs, "rest")
        return msgs

    @property
    def default_prompt(self):
        return self._default_prompt

    @default_prompt.setter
    def default_prompt(self, value):
        self._default_prompt = value

    @property
    def status(self):
        return f"REST: url={self.url}, host={self.host}, model={self.model}, key={self.key}"

    @property
    def system_prompt(self):
        if self.prompt:
            return f"{self.prompt}\n{super().system_prompt} "
        else:
            return super().system_prompt

    @property
    def prompt(self):
        return self._extend_prompt

    @prompt.setter
    def prompt(self, value):
        self._extend_prompt = value


class InsChatBotSimplified(RestChatBot):
    def __init__(self, color_provider, file_title='-', write_out_call_result=None, custom_append=None):
        super().__init__(color_provider, file_title, write_out_call_result, custom_append)


class InsChatBot(InsChatBotObsidianCustom):

    def __init__(self, custom_args: dict = None):
        if custom_args is None:
            custom_args = {}
        bot = InsChatBotSimplified(None, write_out_call_result=self.write_out_continue,
                                   custom_append=self.write_out_obsidian)
        super().__init__(bot, **custom_args)


def create_ins_chat_bot():
    return InsChatBot()
