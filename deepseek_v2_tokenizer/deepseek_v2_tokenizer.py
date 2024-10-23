# pip3 install transformers
# python3 deepseek_v2_tokenizer.py
import os

import transformers


class Tokenizer:
    chat_tokenizer_dir = "deepseek_v2_tokenizer"

    @staticmethod
    def from_pretrained():
        return Tokenizer(Tokenizer.chat_tokenizer_dir)

    def __init__(self, tokenizer_dir="./"):
        tokenizer_dir = os.path.abspath(tokenizer_dir)
        if not os.path.exists(tokenizer_dir):
            raise ValueError(f"Tokenizer directory {tokenizer_dir} not found")
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(tokenizer_dir, trust_remote_code=True)

    def tokenize(self, text):
        tokens = self.tokenizer.encode(text)
        return tokens

    @staticmethod
    def count_tokens(tokens):
        return len(tokens)

    def count(self, text):
        return self.count_tokens(self.tokenize(text))
