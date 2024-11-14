import os

from colorama import Fore, Style

from ChatObsidian.ConsoleChatBot import ConsoleChatBot
from ChatObsidian.flows.obsidian_bot_utils import construct_bot
from ChatObsidian.obsolete_obsidian_utils import system_out, greet
from ChatObsidian.obsolete_obsidian_utils.chat_bot_util import clear_console as cls
from ChatObsidian.obsolete_obsidian_utils.console_chat_extension import process_ai_message, \
    tips_out, is_quit
from Workflow import Step, Monitor, FlowData, StepLoop,get_step_expression


class before_read_msg(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        # ensure bot is ready
        bot = data.get('bot')
        if not bot:
            system_out('Create an initial bot for this console.')
            bot = ConsoleChatBot(post_words=print_console_word)
            data.set('bot', bot)
        pass


class read_msg(Step):
    # example
    # data.set('user_tex', user_tex)
    # data.set('bot_tex', bot_tex)
    # data.set('sys_tex', sys_tex)
    # data.set('fm_tex', fm_tex)
    # data.set('use_nerd_font', use_nerd_font)
    def execute(self, data: FlowData, monitor: Monitor):
        user_mark = data.get('user_tex')
        print(Fore.LIGHTGREEN_EX + user_mark + ': ', end='')
        user_lines = []
        try:
            while True:
                msg = input().strip()
                user_lines.append(msg)
                if not msg.endswith('\\'):
                    break
        except KeyboardInterrupt:
            data.set('input_text', '/new')
            return

        input_text = '\n'.join(user_lines)
        data.set('input_text', input_text)
        pass


class after_read_msg(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        """
        preprocess input message
        known commands:
            /send /post /chat: send a message to chat
            /clear /cls: clear the console
            /bye /exit /quit: quit the console
            / /sw: switch to another bot
            /status /sys: show system status
            /new: start a new chat
            /cmd: exec a cmd
            /quit: quit the console
            /help: show help message
        """
        msg = data.get('input_text').strip()
        action_cmd = 'chat'
        try:
            if not msg:
                action_cmd = 'none'
            elif msg.startswith('/'):
                words = msg[1:].split()
                action_cmd = words[0]
                if len(words) > 1:
                    data.set('arg', words[1:])
            elif is_quit(msg):
                action_cmd = 'quit'
            # @someone msg
            elif msg.startswith('@'):
                # situation 1: @sb
                # situation 2: @sb msg
                # situation 3: @sb:msg
                # situation 4: @sb,msg

                # splitters = [':', ',', ' ']
                # for splitter in splitters:
                #     if spliter in msg:
                #         hint = msg.split(spliter)[0].strip('@')
                #         msg = msg[len(hint) + 1:].strip()

                # for single cmd
                hints = msg[1:].strip()
                data.set('bot_hint', hints)
                action_cmd = 'switch'
                monitor.warning(f'Switch to bot {hints}')
            else:
                if os.path.exists(msg):
                    with open(msg, 'r', encoding='utf-8') as f:
                        msg = f.read()
                ai, dialog = process_ai_message(msg)
                if ai:
                    action_cmd = 'append_system_msg'
                    data.set('ai_text', dialog)
                    # append system message to dialog
                    # out_ai_role_msg(self.fm_name, self.system_name, msg, dialog)
                    pass
                else:
                    action_cmd = 'chat'
                    # self.chat(msg)
                    # try:
                    #     term_width = int(os.get_terminal_size().columns / 3)
                    # except:
                    #     term_width = 100
                    # tips_out(' - ' * term_width)
        except Exception as e:
            if self.is_critical:
                raise e
        data.set('action', action_cmd)


class post_msg(Step):
    # after post
    def execute(self, data: FlowData, monitor: Monitor):
        try:
            width = os.get_terminal_size().columns
            if width > 320:
                width = 320
            term_width = int(width / 3)
        except:
            term_width = 100
        tips_out(' - ' * term_width)
        pass


class after_post_msg(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        pass


# Action on post step

def print_console_word(word: str):
    print(word, end='', flush=True)


class none_step(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        pass


class send_to_chat(Step):
    # with action send post chat
    def execute(self, data: FlowData, monitor: Monitor):
        msg = data.get('input_text').strip()
        if not msg:
            return
        bot_mark = data.get('bot_tex')
        print(Fore.CYAN + bot_mark + ': ', end='')
        bot = data.get('bot')
        if not bot:
            system_out('No bot found, skip chat.')
            return
        try:
            bot.chat(msg)
        # keyboard interrupt
        except KeyboardInterrupt:
            return
        except Exception as e:
            if self.is_critical:
                raise e
        # self.util.chat(msg, context=self.msg_stack)
        print(Style.RESET_ALL)
        pass


class clear_console(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        cls()


class new_chat(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot = data.get('bot')
        bot.new_chat()
        cls()
        print('User clear,stack was cleared. New chat will begin.')
        greet()


class console_exec_cmd(Step):

    @staticmethod
    def prompt(bot):
        if not bot:
            system_out('No bot found, skip exec cmd. Unable to get prompt.')
            return
        try:
            tips_out(f'Prompt: {bot.current_chat.system_prompt}')
        except:
            system_out('No prompt found, skip exec cmd.')

    def execute(self, data: FlowData, monitor: Monitor):
        cmd = data.get('action')
        # for known cmd
        if cmd in ['mpt', 'prompt']:
            bot = data.get('bot')
            self.prompt(bot)
            return

        if cmd in ['set_prompt']:
            return

        if data.has('arg'):
            args = data.get('arg')
            system_out(f'exec cmd: {cmd} {" ".join(args)}')
        else:
            system_out(f'exec cmd: {cmd}')


class sw_bot(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot_arg = data.get('bot_hint')
        if not bot_arg:
            bot = ConsoleChatBot(post_words=print_console_word)
            data.set('bot', bot)
        else:
            su, bot, conf = construct_bot(bot_arg, program=self)
            if su or bot:
                bot._write_out = print_console_word
                data.set('bot', bot)
                if conf:
                    tips_out(f'Switch to bot {bot_arg} with config {conf}')
            else:
                print(f'Cannot find bot {bot_arg}')
                bot = ConsoleChatBot(post_words=print_console_word)
                data.set('bot', bot)


class new_bot(sw_bot):
    pass


class system_status(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot = data.get('bot')
        if not bot:
            system_out('No bot found, skip system status.')
            return
        # ensure bot has properties status
        if not hasattr(bot, 'status'):
            system_out('Bot has no status property, skip system status.')
            system_out(bot)
            return
        print(f'System status: {bot.status}')


class console_help(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        parent_sw_flow = self.parent
        if parent_sw_flow:
            lines = get_step_expression([parent_sw_flow])
            for line in lines:
                tips_out(line)
            print()
        system_out('using /cmd for exec a cmd, /quit to quit, /help for help')


class stop_bot(Step):
    def __init__(self, name, looper: StepLoop):
        super().__init__(name)
        self.looper = looper

    def execute(self, data: FlowData, monitor: Monitor):
        self.looper.stop()
