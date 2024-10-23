import tiktoken


class TaskStatus:
    def __init__(self):
        self.is_complete = False

    def set_complete(self):
        self.is_complete = True


def get_token(content):
    encoding = tiktoken.get_encoding("cl100k_base")
    # 将文本编码为tokens
    tokens = encoding.encode(content)
    return len(tokens)


def wiki_to_markdown(title='Terraria_Wiki', file='', host='https://terraria.wiki.gg/wiki/'):
    pass
