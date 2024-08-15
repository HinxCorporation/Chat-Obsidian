from datetime import datetime


class Message:
    def __init__(self, content: str, user='user', id='0', title=''):
        self.role = user
        self.content = content
        self.id = id
        self.title = title
        self.time = datetime.now()


class Chat:
    def __init__(self):
        self.messages = []
        self.id = 0
        # time is now
        self.time = datetime.now()
        self.title = 'new chat'
        self.model = "model"
        self.system_prompt = "you are a good assistant"
        self.context = ''
