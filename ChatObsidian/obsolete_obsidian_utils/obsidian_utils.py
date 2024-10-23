import json
import os
import re

from .chat_bot_util import generate_uuid, process_text_node, USER_ROLE, BOT_ROLE, SYS_ROLE
from .common import parse_to_filename


def create_new_link_id():
    return "ai_" + generate_uuid()


def generate_obsidian_id(role=''):
    if not role:
        return generate_uuid()
    return f"{role}_{generate_uuid()}"


def obsidian_read_bot_response(file, wdir):
    """
    read bot response from file
    """
    f = obsidian_best_match_file(file, wdir)
    try:
        if f is None or not f:
            return f"Could not find file from {wdir} for {file}"
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8') as file:
                return file.read()
        return f"response file missing :{file} :{wdir} :{f}"
    except Exception:
        return "read response failed"


def obsidian_read_file(file, wdir):
    """
    find file under work dir and read it.
    """
    f = obsidian_best_match_file(file, wdir)
    try:
        if os.path.exists(f):
            with open(f, 'r', encoding='utf-8') as file:
                return f"{file}:\n{file.read()}"
    except:
        pass
    return f"{file}: file not found or cannot read (under {wdir})"


def obsidian_best_match_file(file, wdir):
    """
    find best match file under the work dir
    """
    if os.path.exists(file):
        return os.path.abspath(file)
    try:
        if wdir is None or not wdir:
            raise Exception(f'Root folder is null, unable to search file:{file}')

        # join resolution
        full_dir = os.path.join(wdir, file)
        full_dir = os.path.abspath(str(full_dir))
        if os.path.exists(full_dir):
            return full_dir

        files = obsidian_collect_files(wdir)
        # find the first file name or name without extension that matches the given file name
        _, __short_name = os.path.split(file)
        for f in files:
            folder, filename = os.path.split(f)
            name, ext = os.path.splitext(filename)
            if name in [file, __short_name] or filename in [file, __short_name]:
                return f
            if os.path.basename(f) == file or os.path.splitext(os.path.basename(f))[0] == os.path.splitext(file)[0]:
                return f
    except Exception as e:
        print(e)
    print(f'list file failure: "{file}" in "{wdir}"')
    return ''


def is_obsidian_file(file):
    """
    check if the file is an obsidian file
    """
    return file.endswith('.md') or file.endswith('.canvas')


def obsidian_collect_files(wdir, recursive=True):
    """
    collect all files under the wdir with recursive=True extension with md or canvas
    """
    files = []
    for entry in os.scandir(wdir):
        if entry.is_file() and is_obsidian_file(entry.name):
            files.append(entry.path)
        elif entry.is_dir() and recursive:
            # .ssh and .git .ignore* returns
            if entry.name in ['.ssh', '.git', '.ignore', '.obsidian', '.obsidian_plugins', '.obsidian_cache',
                              '.obsidian_plugins_cache']:
                continue
            if entry.name.startswith('.ignore'):
                continue
            files.extend(obsidian_collect_files(entry.path, True))
    return files


def obsidian_read_node(node) -> [str, []]:
    text = node.get('text', '')
    if not text:
        return "", []
    if text.startswith('system:'):
        text = text[7:].strip()
    elif text.startswith('file:'):
        text = text[5:].strip()
    # get contents from [[ and ]] using regex
    pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(pattern, text)
    # trim text to remove the matched pattern
    text = re.sub(pattern, '', text)
    # read file list from the matched files
    files = [m.strip() for m in matches if m.strip()]
    return text, files


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
    relative_file = get_relative_file_obsidian(full_path, obsidian_dir)

    currentNode, trans = create_response_node(blank_node, relative_file)
    y_assistant, chat_color = util.get_color('assistant_dialog')
    if y_assistant:
        currentNode = {**currentNode, "color": chat_color}
        trans = {**trans, "color": chat_color}

    blank_node['text'] = text
    b_id = blank_node['id']
    if '_' not in b_id:
        blank_node['id'] = f"{USER_ROLE}_{b_id}"
    y_user, user_color = util.get_color('user_dialog')
    if y_user and user_color != '0':
        # set or add color field as color
        blank_node['color'] = user_color

    nodes.append(currentNode)
    edges.append(trans)

    y, c = util.get_color('system_dialog')
    flush_canvas_file(file, nodes, edges, y, c)
    return full_path, text


def get_relative_file_obsidian(full_path, obsidian_dir):
    if not obsidian_dir:
        print(f'obsidian_dir is null, unable to get relative file for {full_path}')
        return full_path
    return os.path.relpath(str(full_path), obsidian_dir).replace('\\', '/')


def create_response_node(blank_node, file, color_str: str = None):
    trans_id = generate_obsidian_id("ai-response")
    # current_chat = obsidian_dir + '/' + relative_file

    new_id = generate_obsidian_id(BOT_ROLE)
    # config rectangle
    offset_y = 15
    new_wid = 880
    new_hei = 600
    ori_x = blank_node.get('x', 0)
    ori_y = blank_node.get('y', 0)
    ori_width = blank_node.get('width', 0)
    ori_height = blank_node.get('height', 0)
    new_x = ori_x + ori_width - new_wid
    new_y = ori_y + ori_height + offset_y
    # chat_color =
    if not color_str:
        color_str = '#7e38ff'

    currentNode = {
        'id': new_id,
        'x': new_x,
        'y': new_y,
        'width': new_wid,
        'height': new_hei,
        'type': 'file',
        'file': file,
        "color": color_str
    }
    trans = {
        'id': trans_id,
        'fromNode': blank_node['id'],
        'toNode': new_id,  # Assuming you want to connect to the original node
        'fromSide': 'bottom',
        'toSide': 'top',
        "color": color_str
    }
    return currentNode, trans


def flush_canvas_file(file, nodes, edges, y_system, system_color):
    """
    flush canvas file with new nodes and edges
    """
    if y_system:
        for node in nodes:
            if node.get('type') == 'text':
                nt = node.get('text')
                if nt.startswith('system:') or nt.startswith('file:'):
                    node['color'] = system_color

    # Write the updated graph data back to the file
    with open(file, 'w', encoding='utf-8') as fs:
        canvas = {'nodes': nodes, 'edges': edges}
        json_str = json.dumps(canvas, indent=4)
        fs.write(json_str)


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


def read_node_content(node, wdir):
    if node['type'] == 'file':
        relative_file = node['file']
        file_path = os.path.join(wdir, relative_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return 'missing reference message'
    elif node['type'] == 'text':
        # text may contains extra order
        return str(node['text'])


def node_to_message_base_on_node_id(node, wdir):
    node_id = node['id']
    role = node_id[0:node_id.index('_')]
    content = read_node_content(node, wdir)
    if role in [USER_ROLE, BOT_ROLE, SYS_ROLE]:
        return {
            'block_type': 'text',
            'role': role,
            'content': content
        }
    return {
        'block_type': 'unknown',
        'role': role,
        'content': content
    }


def node_to_message(node, wdir):
    # work dir is wdir , reference file under the work dir.
    # {"id":"1","type":"text","text":"文","color":"#rrggbb"},
    # {"x":-482,"y":-415,"width":382,"height":60}
    node_id = node['id']
    if '_' in node_id:
        return node_to_message_base_on_node_id(node, wdir)
    # the resolution base on node type
    if node['type'] == 'file':
        relative_file = node['file']
        file_path = os.path.join(wdir, relative_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return {'content': content,
                        "role": "assistant"}
        except:
            return {'content': 'missing reference message',
                    "role": "system"}
    elif node['type'] == 'text':
        content = str(node['text'])
        return process_text_node(content, wdir)


def create_node_chain(current, nodes, edges):
    """
    complete the chain from current node to the beginning of the graph ,
    current node is excluded.
    returns node chain
    """
    prev = get_pre(current, nodes, edges)
    if prev:
        return [*pre_chain(prev, nodes, edges, []), prev]
    else:
        return []


def create_message_chain(current, nodes, edges, wdir):
    """
    complete the chain from current node to the beginning of the graph ,
    current node is excluded.
    returns washed message chain
    """
    prev = get_pre(current, nodes, edges)
    if prev:
        # chain = [prev, *pre_chain(prev, nodes, edges, [])]
        chain = [*pre_chain(prev, nodes, edges, []), prev]
        # print('\n'.join([c.get('id') for c in chain]))
        return [node_to_message(node, wdir) for node in chain]
    else:
        return []


def validate_chat_node(node, from_ids):
    """validate a chat node, if it is free to use and not empty"""
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
