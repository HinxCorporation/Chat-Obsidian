from Chat.common import *
from PyChatBot.chat_bot_util import *


def process_relative_block(util, nodes, edges, blank_node, file, obsidian_dir):
    """
    process a block of an obsidian file block
    :param util:
    :param nodes:
    :param edges:
    :param blank_node:
    :param file:
    :param obsidian_dir:
    :return:
    """
    text = str(blank_node['text']).strip().strip('\\')
    canvas_folder, canvasName = os.path.split(file)
    full_path = os.path.join(canvas_folder, f'dialog\\{canvasName}.ai.assets',
                             parse_to_filename(text, 46) + f'.md')
    # relative_file = 'AI-Chat/dialog/{canvasName}.ai.assets/' + util.parse_to_filename(text, 46) + f'.md'
    relative_file = os.path.relpath(str(full_path), obsidian_dir).replace('\\', '/')
    new_id = generate_uuid()
    trans_id = generate_uuid()
    # current_chat = obsidian_dir + '/' + relative_file

    # config rectangle
    offset_y = 5
    new_wid = 880
    new_hei = 600
    ori_x = blank_node.get('x', 0)
    ori_y = blank_node.get('y', 0)
    ori_width = blank_node.get('width', 0)
    ori_height = blank_node.get('height', 0)
    new_x = ori_x + ori_width - new_wid
    new_y = ori_y + ori_height + offset_y
    # chat_color = '#7e38ff'
    y_assistant, chat_color = util.get_color('assistant_dialog')

    currentNode = {
        'id': new_id,
        'x': new_x,
        'y': new_y,
        'width': new_wid,
        'height': new_hei,
        'type': 'file',
        'file': relative_file
        # ,
        # "color": chat_color
    }
    trans = {
        'id': trans_id,
        'fromNode': blank_node['id'],
        'toNode': new_id,  # Assuming you want to connect to the original node
        'fromSide': 'bottom',
        'toSide': 'top'
        # ,
        # "color": chat_color
    }
    if y_assistant:
        currentNode = {**currentNode, "color": chat_color}
        trans = {**trans, "color": chat_color}

    blank_node['text'] = text
    y_user, user_color = util.get_color('user_dialog')
    if y_user and user_color is not '0':
        # set or add color field as color
        blank_node['color'] = user_color

    nodes.append(currentNode)
    edges.append(trans)

    y_system, system_color = util.get_color('system_dialog')
    if y_system:
        for node in nodes:
            if node.get('type') == 'text':
                nt = node.get('text')
                if nt.startswith('system:') or nt.startswith('file:'):
                    node['color'] = system_color

    # Write the updated graph data back to the file
    with open(file, 'w', encoding='utf-8') as f:
        json.dump({'nodes': nodes, 'edges': edges}, f)
    return full_path, text


def get_pre(current, nodes, edges):
    """
    获取上一个节点
    """
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
    # work dir is wdir , reference file under the work dir.
    # {"id":"1","type":"text","text":"文","color":"#rrggbb"},
    # {"x":-482,"y":-415,"width":382,"height":60}
    if node['type'] == 'file':
        relative_file = node['file']
        file_path = os.path.join(wdir, relative_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return {'content': content,
                        "role": "assistant"}
        except:
            return {'content': 'missing message',
                    "role": "system"}
    elif node['type'] == 'text':
        content = str(node['text'])
        return process_text_node(content, wdir)


def create_message_chain(current, nodes, edges, wdir):
    prev = get_pre(current, nodes, edges)
    if prev:
        # chain = [prev, *pre_chain(prev, nodes, edges, [])]
        chain = [*pre_chain(prev, nodes, edges, []), prev]
        # print('\n'.join([c.get('id') for c in chain]))
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
