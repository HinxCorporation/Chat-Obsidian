# listen to a canvas file , and make sure all content has response.
import os.path
import time
from pathlib import Path

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from Chat.Queue import Queue
from Chat.chatutil import *
from Chat.obsidian_utils import *

current_chat = ''
queue = Queue()


class WatcherHandler(PatternMatchingEventHandler):
    def __init__(self):
        # Ignore everything but .txt files, and directories named .idea and .git
        super().__init__(ignore_patterns=["*/.idea/*", '*/venv/*', "*/.git/*", "*/\.*", ".ignore*"],
                         ignore_directories=True)

    # Event handlers here, for example:
    def on_modified(self, event):
        global queue
        src_path = event.src_path
        if not queue.__contains__(src_path):
            queue.enqueue(src_path)

    def on_created(self, event):
        src_path = event.src_path
        if not queue.__contains__(src_path):
            queue.enqueue(src_path)


def print_context(context):
    print('---------------------context-------------------------')
    try:
        for msg in context:
            role = msg.get('role')
            content = msg.get('content')
            if len(content) > 64:
                content = content[:61] + '...'
            print(role, ':', content)
            print('-------------------------------------------------------------')
    except:
        pass


def process_canvas_file(file, util, note_root):
    """
    file is canvas file
    """
    # try:
    with open(file, 'r', encoding='utf-8') as f:
        json_dat = json.load(f)
        nodes = json_dat['nodes']
        edges = json_dat['edges']

    ids = set()
    for e in edges:
        ids.add(e['fromNode'])
    global current_chat
    goes_to_chat = [n for n in nodes if validate_chat_node(n, ids)]
    i_len = len(goes_to_chat)
    if i_len > 0:
        print(f'new chat: {i_len}')
        for blank_node in goes_to_chat:
            current_chat, text = process_relative_block(util, nodes, edges, blank_node, file, note_root)
            print(f'begin chat : {text} , update it to {current_chat}')
            context = create_message_chain(blank_node, nodes, edges, note_root)
            # print(context)
            print_context(context)
            util.chat(text, context)
            time.sleep(2)
    else:
        pass
    current_chat = ''


def begin_observe(directory_to_scan):
    if not os.path.exists(directory_to_scan):
        os.makedirs(directory_to_scan)
    print('Console Gonna stop ctrl + c to exit')
    event_handler = WatcherHandler()
    observer = Observer()
    print(f'notes listen will runs on :{directory_to_scan}')
    observer.schedule(event_handler, directory_to_scan, recursive=True)
    observer.start()
    return observer


def initialize_config():
    config_file = Path('config.ini')
    if not config_file.is_file():
        print('config.ini file does not exist')
        return False, '', ''

    config = configparser.ConfigParser()
    try:
        config.read(config_file, encoding='utf-8')
    except configparser.ParsingError as e:
        print('Could not parse config.ini:', str(e))
        return False, '', ''

    try:
        note_root = Path(config.get('setting', 'note_root', fallback='')).resolve(strict=True)
    except FileNotFoundError as e:
        print('note_root does not exist:', str(e))
        return False, '', ''
    except KeyError as e:
        print('note_root does not exist in config.ini:', str(e))
        return False, '', ''

    try:
        chat_folders = config.get('setting', 'chat_folders', fallback='')
    except KeyError as e:
        print('chat_folders does not exist in config.ini:', str(e))
        return False, '', ''

    if not chat_folders:
        chat_folders = 'AI-Chat'

    return True, str(note_root), chat_folders.split(',')


def setup_observers(note_root, folders_list):
    observers = []
    for sub_folder in folders_list:
        directory_to_scan = os.path.join(note_root, sub_folder)
        observers.append(begin_observe(directory_to_scan))  # use append for lists
    return observers


def run_observers(observers, **kwargs):
    try:
        while True:
            while queue.has_next():
                process_files(queue.dequeue(), **kwargs)
            time.sleep(0.5)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        print('user stopped observers')
    for observer in observers:
        observer.join()


def process_files(file_path, **kwargs):
    _, extension = os.path.splitext(file_path)
    if extension == '.canvas':
        try:
            process_canvas_file(file_path, **kwargs)
        except Exception as e:
            print('processing file error')
            print(e)


def main():
    success, note_root, folders_list = initialize_config()
    if not success:
        return

    def write_out(json_str: str):
        global current_chat
        if not current_chat:
            return
        folder, _ = os.path.split(current_chat)
        if not os.path.exists(folder):
            os.makedirs(folder)

        w = get_words_deep_seek_bot(json_str)
        print(w, end='')
        with open(current_chat, 'a', encoding='utf-8') as flush_char_f:
            # write content with sample line
            flush_char_f.write(w)
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


if __name__ == "__main__":
    main()
