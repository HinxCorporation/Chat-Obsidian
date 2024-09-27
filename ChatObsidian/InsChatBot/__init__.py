from .ins_chat_bot_custom import InsChatBotObsidianCustom as InsCustom
from .ins_chat_bot_generic import InsChatBotGeneric
from .ins_chat_bot_instance import InsChatBot as InsBot, RestChatBot as RestBot, OpenAIChatBot as OpenAIBot, \
    OllamaChatBot as OllamaBot
from .ins_chat_bot_instance import create_ins_chat_bot
from .ins_chat_bot_shell import InsChatBotShell as InsShell

__all__ = [
    'InsChatBotGeneric',
    'InsBot',
    'InsShell',
    'create_ins_chat_bot',
    'OpenAIBot',
    'OllamaBot',
    'RestBot',
    'InsCustom'
]
