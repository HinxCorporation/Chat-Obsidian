# listen to a canvas file , and make sure all content has response.

from .ObsidianShared import *
from .WatcherUtil import *


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
        return

    observers = setup_observers(note_root, folders_list)
    run_observers(observers, util=util, note_root=note_root)
    print('program quit.')
