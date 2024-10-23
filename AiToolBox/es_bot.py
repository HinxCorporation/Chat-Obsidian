from PyAissistant.PyChatBot.deep_seek_bot import DeepSeekBot
import json
from deepseek_v2_tokenizer import Tokenizer


class ESbot(DeepSeekBot):
    def __init__(self, tokenizer=None):
        super().__init__(self.print_response, function_call_feat=True)
        if tokenizer is not None:
            self.tokenizer = tokenizer
        else:
            self.tokenizer = Tokenizer.from_pretrained()
        # self.tokenizer = Tokenizer()
        # self.stream = False

    def setup_function_tools(self):
        self.executor.add_tool(self.post_es)
        print("ESbot function tools setup complete")
        pass

    def post_es(self, **kwargs):
        """
        This method is used to push the knowledge entries extracted from the document to the ES server.
        :param kwargs:
        :return: success or error message
        """
        print("################Posting to ES server...################")
        if self.stream:
            pass
        print(kwargs)
        return "success"

    @staticmethod
    def print_response(word):
        print(word, end="")
        pass

    def _finish_deep_seek_payload(self, chain):
        if self.function_call_features:
            tools_exists = self.tools is not None and len(self.tools) > 0
            if tools_exists:
                return json.dumps({
                    "messages": chain,
                    "model": self.model,
                    "frequency_penalty": 0,
                    "max_tokens": self.max_tokens,
                    "presence_penalty": 0,
                    "stop": None,  # stop continue while this word is generated
                    "stream": self.stream,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "tools": self.tools,
                    "tool_choice": 'required',
                    "logprobs": False,
                    "top_logprobs": None
                })

    def get_organize_hints(self):
        if self.stream:
            pass
        return ("""Your Responsibilities:
To understand and process the received documents, pushing the knowledge within the documents one piece at a time to our search engine (ES).

You Need:

Familiarity with the structure and content of the documents to accurately extract knowledge entries.
Mastery of the post_es method, which is crucial for pushing knowledge entries to ES.
Ensuring that the document content is correctly segmented into individual knowledge entries before pushing.
Work Process:

Receive the Document:

First, receive and review the documents assigned to you.
Understand Document Content:

Carefully read the document to understand its subject matter and the knowledge entries it contains.
Document Preprocessing:

Perform necessary preprocessing on the document, such as format conversion and encoding correction, to ensure the content can be correctly parsed.
Content Segmentation:

Based on the structure of the document, segment it into individual knowledge entries. This may involve identifying titles, paragraphs, list items, etc.
Knowledge Entry Extraction:

Extract knowledge entries from each segmented part, ensuring each entry is complete and contains all necessary information.
Invoke the post_es Method:

For each extracted knowledge entry, invoke the post_es method to push it to ES.
Ensure that all necessary parameters are correctly set when calling the method, such as the entry's ID, content, tags, etc.
Error Handling:

If errors are encountered during the push process, record them and attempt to resolve or escalate to technical support.
Documentation and Reporting:

Keep a record of all successfully pushed entries and any issues encountered.
At the end of the work, write a brief report summarizing your results and any problems encountered.
Feedback and Improvement:

Continuously improve your workflow and methods based on feedback to increase efficiency and accuracy.
Ensure that you maintain attention to detail and focus during each step to guarantee that the knowledge entries pushed to ES are accurate and valuable.
        """)

    def post(self, file: str):
        # read content from file
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        # tokenize content
        tokenized_content = self.tokenizer.tokenize(content)
        # generate response
        length = len(tokenized_content)
        if length > self.max_tokens*10:
            return "Sorry, the content is too long for me to understand. Please provide a shorter message." + \
                       f"\nCurrent:{length} tokens , Max:{self.max_tokens} tokens"
        else:
            self.new_chat()
            self.post_prompt(self.get_organize_hints())
            return self.chat(f"请处理这个文档并且推送到ES服务器。以下是文档内容\n{content}")

