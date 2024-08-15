# listen to a canvas file , and make sure all content has response.
import os.path

from .WatcherUtil import *
from .Queue import Queue

current_chat = ''
queue = Queue()


def run():
    success, note_root, folders_list = initialize_config()
    if not success:
        return

    def write_out(bot_words: str):
        global current_chat
        if not current_chat:
            return

        folder, _ = os.path.split(current_chat)
        if not os.path.exists(folder):
            os.makedirs(folder)

        print(bot_words, end='')
        with open(current_chat, 'a', encoding='utf-8') as flush_char_f:
            # write content with sample line
            flush_char_f.write(bot_words)
        pass

    try:
        util = ChatUtil(write_out)
        # util.cache_transitions = True
    except Exception as e:
        print('initialize failure. pls check your config file.')
        # raise e
        print(e)
        return

    observers = setup_observers(note_root, folders_list)
    run_observers(observers, util=util, note_root=note_root)
    print('program quit.')
