from .Chat import *
from .chat_bot_util import *


class ChatBot:
    def __init__(self, write_out):
        self.current_chat: Chat
        self.current_chat = None
        self.chats = []
        self.new_chat()
        self._write_out = write_out

    def new_chat(self):
        self.current_chat = Chat()
        self.current_chat.id = generate_uuid(32)
        self.chats.append(self.current_chat)

    def post_prompt(self, prompt: str):
        """Set the system prompt for the chat bot."""
        self.current_chat.system_prompt = prompt

    def chat(self, message: str):
        """Handle incoming messages and manage the conversation."""
        usr_mgs = Message(message)
        usr_mgs.id = generate_uuid(28)
        self.current_chat.messages.append(usr_mgs)
        response, dialog_id = self._generate_response(message)
        bot_msg = Message(response, BOT_ROLE, id=dialog_id)
        self.current_chat.messages.append(bot_msg)
        return response

    def _generate_response(self, message: str) -> [str, str]:
        """Generate a response based on the incoming message."""
        # Placeholder for actual response generation logic
        return f"Echo: {message}", 'id'

    def message_chain(self):
        return [*self.get_system_prompt(), *[get_message(m.content, m.role) for m in self.messages]]

    def get_system_prompt(self) -> []:
        return [get_message(self.system_prompt, SYS_ROLE)]

    @property
    def messages(self):
        """List of messages in the conversation."""
        return self.current_chat.messages

    @property
    def system_prompt(self):
        """The system prompt for the chat bot."""
        return self.current_chat.system_prompt

    @property
    def context(self):
        """The context of the conversation."""
        return self.current_chat.context

    @context.setter
    def context(self, value: dict):
        self.current_chat.context = value
