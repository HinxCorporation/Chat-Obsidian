import json
import os
import uuid


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
