# listen to a canvas file , and make sure all content has response.
import time

from Chat.chatutil import *
from Chat.obsidian_utils import *


def main():
    note_root = ''
    try:
        config_file = 'config.ini'
        config = configparser.ConfigParser()
        config.read(config_file)
        note_root = config.get("setting", "note_root", fallback='')
        note_root = os.path.abspath(note_root)
    except configparser.NoSectionError:
        pass

    if not note_root:
        print('needs to setup a note root on config.ini file')
        return

    def write_out(json_str: str):
        w = get_words(json_str)
        if not current_chat:
            return
        folder, _ = os.path.split(current_chat)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(current_chat, 'a', encoding='utf-8') as flush_char_f:
            # write content with sample line
            flush_char_f.write(w)
        pass

    util = ChatUtil(write_out)

    directory_to_scan = note_root + '/AI-Chat/'
    if not os.path.exists(directory_to_scan):
        os.makedirs(directory_to_scan)
    print('Console Gonna stop ctrl + c to exit')
    while True:
        # scan only top files. with canvas.
        for entry in os.scandir(directory_to_scan):
            if entry.is_dir():
                pass
            elif entry.is_file() and entry.path.endswith('.canvas'):
                # try:
                file = entry.path
                with open(file, 'r', encoding='utf-8') as f:
                    json_dat = json.load(f)
                    nodes = json_dat['nodes']
                    edges = json_dat['edges']

                ids = set()
                for e in edges:
                    ids.add(e['fromNode'])
                    # ids.add(e['toNode'])

                goes_to_chat = [n for n in nodes if validate_chat_node(n, ids)]
                i_len = len(goes_to_chat)
                if i_len > 0:
                    print(f'new chat: {i_len}')
                    for blank_node in goes_to_chat:
                        current_chat, text = process_relative_block(util, nodes, edges, blank_node, file, note_root)
                        print(f'begin chat : {text}')
                        context = create_message_chain(blank_node, nodes, edges, note_root)
                        print(context)
                        util.chat(text, context)
                        time.sleep(2)
                else:
                    print(f'.', end='', flush=True)
                    pass
                # except Exception as e:
                #     print(e)
                #     pass
                current_chat = ''
        time.sleep(1)


if __name__ == "__main__":
    main()
