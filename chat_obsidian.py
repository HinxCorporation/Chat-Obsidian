# listen to a canvas file , and make sure all content has response.
import configparser
import json
import os
import time
import uuid

import chatutil


def generate_uuid():
    # def length = 32
    return str(uuid.uuid4()).replace('-', '')[:12]


def process_relative_block(util, nodes, edges, blank_node, file: str, obsidian_dir: str):
    text = str(blank_node['text']).strip().strip('\\')
    _, canvasName = os.path.split(file)
    relative_file = f'AI-Chat/dialog/{canvasName}.ai.assets/' + util.parse_to_filename(text, 46) + f'.md'
    new_id = generate_uuid()
    trans_id = generate_uuid()
    current_chat = obsidian_dir + '/' + relative_file
    currentNode = {
        'id': new_id,
        'x': blank_node.get('x', 0),
        'y': blank_node.get('y', 0) + 300,
        'width': 1280,
        'height': 600,
        'type': 'file',
        'file': relative_file
    }
    trans = {
        'id': trans_id,
        'fromNode': blank_node['id'],
        'toNode': new_id,  # Assuming you want to connect to the original node
        'fromSide': 'bottom',
        'toSide': 'top'
    }

    blank_node['text'] = text
    nodes.append(currentNode)
    edges.append(trans)

    # Write the updated graph data back to the file
    with open(file, 'w', encoding='utf-8') as f:
        json.dump({'nodes': nodes, 'edges': edges}, f)
    return current_chat, text


def get_words(content: str):
    try:
        json_obj = json.loads(content)
        content = json_obj['choices'][0]['delta']['content']
        return content
    except Exception as ee:
        return '-'


def get_pre(current, nodes, edges):
    current_id = current['id']
    to_current_ids = [e['fromNode'] for e in edges if e['toNode'] == current_id]
    try:
        if len(to_current_ids) == 1:
            sid = to_current_ids[0]
            pre = next((n for n in nodes if n['id'] == sid), None)
            if pre:
                return pre
        return None
    except:
        return None


def pre_chain(current, nodes, edges, chain):
    prev_node = get_pre(current, nodes, edges)
    if prev_node:
        chain = [prev_node] + chain  # prepend to chain
        return pre_chain(prev_node, nodes, edges, chain)
    return chain


def node_to_message(node, wdir):
    # {"id":"1","type":"text","text":"t ","x":-482,"y":-415,"width":382,"height":60,"color":"1"},
    if node['type'] == 'file':
        relative_file = node['file']
        file_path = os.path.join(wdir, relative_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return {
                    'content': content,
                    "role": "assistant"
                }
        except:
            return {
                'content': 'missing message',
                "role": "system"
            }
    elif node['type'] == 'text':
        content = node['text']
        return {
            'content': content,
            "role": "user"
        }


def create_message_chain(current, nodes, edges, wdir: str):
    prev = get_pre(current, nodes, edges)
    if prev:
        chain = pre_chain(prev, nodes, edges, [])
        return [node_to_message(node, wdir) for node in chain]
    else:
        return []


def validate_chat_node(node, from_ids):
    free_used = node['id'] not in from_ids
    if not free_used:
        return False
    if node['type'] == 'file':
        return False
    text = node.get('text', '')
    if not text:
        return False
    if text.endswith('\\'):
        return True
    return False


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

    util = chatutil.ChatUtil(write_out)

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
