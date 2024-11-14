# import configparser

from colorama import Style

from Workflow import Monitor
from .flows_console import create_flow_console_app
from .obsolete_obsidian_utils import clear_console, ConsoleChat, system_out, greet, bye


def run():
    system_out("This command is obsolete. Please use 'new chat flow' instead.")
    console_chat_flow = create_flow_console_app()
    console_chat_flow.preview()
    print()
    print("Any key (return) to start the chat flow...")
    input()
    clear_console()
    monitor = Monitor('Chat Console monitor', skip_info=True)
    try:
        console_chat_flow.run(flow_name="Enjoy your console chat with bot!", custom_monitor=monitor)
    except KeyboardInterrupt:
        system_out("Chat flow stopped by user.")


def run_obsolete():
    user_tex = 'User'
    bot_tex = 'Bot'
    sys_tex = "System"
    fm_tex = 'file'
    use_nerd_font = ""
    clear_console()

    # try:
    #     config_file = 'config.ini'
    #     config_content = read_config_file(config_file)
    #     config = configparser.ConfigParser()
    #     config.read_string(config_content)
    #
    #     use_nerd_font = config.get('Console', 'use_nerd_font', fallback='false').lower() == 'true'
    #     if use_nerd_font:
    #         user_tex = config.get('NERD', 'char_avatar', fallback=user_tex)
    #         bot_tex = config.get('NERD', 'char_bot', fallback=bot_tex)
    #         sys_tex = config.get('NERD', 'char_computer', fallback=sys_tex)
    #         fm_tex = config.get('NERD', 'char_folder', fallback=fm_tex)
    #         pass
    #
    # except Exception as e:
    #     print(f"An error occurred while reading the config file: {e}")

    if use_nerd_font:
        system_out(f'{sys_tex} Now are using NERD font. enjoy.')
    else:
        system_out(f'{sys_tex} welcome')

    console_bot = ConsoleChat(user_tex, bot_tex, sys_tex, fm_tex)

    greet()
    while console_bot.running:
        try:
            console_bot.loop()
        except KeyboardInterrupt:
            # reset style on interrupt
            print(Style.RESET_ALL, end='')
            console_bot.new_dialog()
    bye()
