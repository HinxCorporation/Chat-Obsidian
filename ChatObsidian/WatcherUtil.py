import os.path
import time
from pathlib import Path

from .ObsidianShared import *

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from .obsolete_obsidian_utils.chatutil import *
from .obsolete_obsidian_utils.obsidian_utils import *
from .chat_obsidian import *


class WatcherHandler(PatternMatchingEventHandler):
    def __init__(self):
        # Ignore everything but .txt files, and directories named .idea and .git
        super().__init__(ignore_patterns=["*/.idea/*", '*/venv/*', "*/.git/*", "*/\.*", ".ignore*"],
                         ignore_directories=True)

    # Event handlers here, for example:
    def on_modified(self, event):

        src_path = event.src_path
        if not current.queue.__contains__(src_path):
            current.queue.enqueue(src_path)

    def on_created(self, event):
        src_path = event.src_path
        if not current.queue.__contains__(src_path):
            current.queue.enqueue(src_path)


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

    goes_to_chat = [n for n in nodes if validate_chat_node(n, ids)]
    i_len = len(goes_to_chat)
    if i_len > 0:
        print(f'new chat: {i_len}')
        for blank_node in goes_to_chat:
            current.current_chat, text = process_relative_block(util, nodes, edges, blank_node, file, note_root)
            print(f'begin chat : {text} , update it to {current.current_chat}')
            context = create_message_chain(blank_node, nodes, edges, note_root)
            # print(context)
            print_context(context)
            util.chat(text, context)
            time.sleep(2)
    else:
        pass
    current.current_chat = ''


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
            while current.queue.has_next():
                process_files(current.queue.dequeue(), **kwargs)
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
