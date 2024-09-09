# listen to a canvas file , and make sure all content has response.

from .WatcherUtil import initialize_config, setup_observers, run_observers
from .obsolete_obsidian_utils.chatutil import ChatUtil


def run():
    success, note_root, folders_list = initialize_config()
    if not success:
        return

    try:
        util = ChatUtil()
        # util.cache_transitions = True
    except Exception as e:
        print('initialize failure. pls check your config file.')
        # raise e
        print(e)
        raise e

    observers = setup_observers(note_root, folders_list)
    # print a green color message to indicate the program is running.
    print('\033[92m' + 'ChatObsidian is running...\nConsole Gonna stop, ctrl + c to exit\n' + '\033[0m')
    run_observers(observers, util=util, note_root=note_root)
    print('program quit.')
