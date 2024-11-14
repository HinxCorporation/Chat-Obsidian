import configparser

from Workflow import WorkflowBuilder, Step, Monitor, FlowData, StepLoop, SwitchStep, separate_console_line
from .console_chat_loop import before_read_msg, read_msg, after_read_msg, post_msg, after_post_msg
from .console_chat_loop import send_to_chat, clear_console as clear_console_step, new_chat, sw_bot, system_status, \
    console_help, stop_bot, console_exec_cmd, none_step
from ..obsolete_obsidian_utils import clear_console, system_out, read_config_file, greet


def create_flow_console_app():
    return (WorkflowBuilder()
            .add_step(_app_greeting("Welcome to ChatObsidian!"))
            .add_step(_app_init("Console AppInitializing..."))
            .add_step(_app_start("Console App Starting...", is_critical=True))
            .add_step(_app_loop("Console App Entering loop..."))
            .add_step(_app_end("Bye bye!"))
            .build())


class _app_greeting(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        clear_console()
        system_out(separate_console_line(greet(), special_char='='))
        pass


class _app_init(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        user_tex = 'User'
        bot_tex = 'Bot'
        sys_tex = "System"
        fm_tex = 'file'
        use_nerd_font = ""

        try:
            config_file = 'config.ini'
            config_content = read_config_file(config_file)
            config = configparser.ConfigParser()
            config.read_string(config_content)

            use_nerd_font = config.get('Console', 'use_nerd_font', fallback='false').lower() == 'true'
            if use_nerd_font:
                user_tex = config.get('NERD', 'char_avatar', fallback=user_tex)
                bot_tex = config.get('NERD', 'char_bot', fallback=bot_tex)
                sys_tex = config.get('NERD', 'char_computer', fallback=sys_tex)
                fm_tex = config.get('NERD', 'char_folder', fallback=fm_tex)
                pass
        except Exception as e:
            print(f"An error occurred while reading the config file: {e}")

        data.set('user_tex', user_tex)
        data.set('bot_tex', bot_tex)
        data.set('sys_tex', sys_tex)
        data.set('fm_tex', fm_tex)
        data.set('use_nerd_font', use_nerd_font)

        if use_nerd_font:
            system_out(f'{sys_tex} Now are using NERD font. enjoy.')
        else:
            system_out(f'{sys_tex} welcome')


class _app_start(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        pass


class _app_loop(StepLoop):
    def __init__(self, message: str):
        super().__init__(message, True)
        send_msg_cmds = ['send', 'post', 'chat']
        cls_cmds = ['clear', 'cls']
        exit_cmds = ['bye', 'exit', 'quit', 'q', 'stop']
        self.add_step(before_read_msg("Before read message"))
        self.add_step(read_msg("read message from console"))
        self.add_step(after_read_msg("After read message,processing them and put to console"))
        self.add_step(SwitchStep("post", 'action')
                      .add_case_multi(send_msg_cmds, send_to_chat("send message to chat"))
                      .add_case_multi(cls_cmds, clear_console_step("clear console"))
                      .add_case("new", new_chat("create new chat"))
                      .add_case("switch", sw_bot("switch bot"))
                      .add_case("help", console_help("help"))
                      .add_case_multi(exit_cmds, stop_bot("stop bot", self))
                      .add_case("status", system_status("system status"))
                      .add_case("none", none_step("skip"))
                      .add_default(console_exec_cmd("Execute command in console"))
                      )
        self.add_step(post_msg("After post them, Waiting for response and exit"))
        self.add_step(after_post_msg("After post message,processing them and put to console"))


class _app_end(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        pass
