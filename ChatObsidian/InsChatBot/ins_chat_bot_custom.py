import os

from .ins_chat_bot_shell import InsChatBotShell, ROOT_DIR
from ..obsolete_obsidian_utils import get_relative_file_obsidian


class InsChatBotObsidianCustom(InsChatBotShell):
    def __init__(self, bot, **kwargs):
        super().__init__(bot, kwargs)
        _col_provider_method = getattr(self.bot, 'color_provider', None)
        if _col_provider_method:
            self.set('color_provider', _col_provider_method)

    def write_out_continue(self, function_name, kwargs, exec_result):
        call_result_file = self.get_current_append_file(create_type='.call_result')
        folder, _ = os.path.split(call_result_file)
        os.makedirs(folder, exist_ok=True)

        # after function calls , write out call result to file.
        working_dir = self.get(ROOT_DIR)
        with open(call_result_file, 'a', encoding='utf-8') as call_result_f:
            call_result_f.write(f'-------------------------------------------\n')
            call_result_f.write(f'#### call:{function_name}\n')
            call_result_f.write(f'- input: {kwargs}\n')
            call_result_f.write(f'- output: {exec_result}\n')
            call_result_f.write(f'\n')

        relative_file = get_relative_file_obsidian(os.path.abspath(call_result_file),
                                                   os.path.abspath(working_dir))
        self.write_out_obsidian(f'\n> Done. [RES.]({relative_file}) \n\n')

    def apply_additional_settings(self, config):
        errors = []
        success = []
        ignores = []
        for key, value in config.items():
            if hasattr(self, key):
                try:
                    # blue_print(f' \tUpdate bot with: {key}')
                    setattr(self, key, value)
                    success.append(f' \tSET:{key} Success')
                except:
                    errors.append(f' \tSET:{key} Failure by {value}')
                    pass
            else:
                ignores.append(f' \tSET:{key} Ignored')
                pass
        return errors, success, ignores
