from PyAissistant.PyChatBot.deep_seek_bot import DeepSeekBot


class ConsoleChatBot(DeepSeekBot):

    def __init__(self, post_words, post_function_calls=None):
        super().__init__(post_words, function_call_feat=True)
        self.post_function_calls = post_function_calls

    def execute_func(self, function_tool, **kwargs):
        exec_result = super().execute_func(function_tool, **kwargs)
        if self.post_function_calls:
            tool_details = function_tool['function']
            function_name = tool_details['name']
            self.post_function_calls(f'-------------------------------------------\n')
            self.post_function_calls(f'#### call:{function_name}\n')
            self.post_function_calls(f'- input: {kwargs}\n')
            self.post_function_calls(f'- output: {exec_result}\n')
            self.post_function_calls(f'\n')
        return exec_result
