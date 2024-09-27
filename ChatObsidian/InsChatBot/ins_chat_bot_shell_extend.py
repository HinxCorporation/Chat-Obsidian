import uuid

from PyAissistant import Message

from ..obsolete_obsidian_utils import obsidian_read_node, \
    obsidian_read_file, BOT_ROLE, USER_ROLE, obsidian_read_bot_response


def measure_string(text, padding, char_unit_size, max_width=None, fixed_width=None):
    """
    Measures the string for the canvas node block
    """
    char_width, char_height = char_unit_size
    top_padding, bottom_padding, left_padding, right_padding = padding

    # Use fixed width if provided, otherwise determine based on max_width
    if fixed_width:
        width = fixed_width
    elif max_width:
        width = min(max(len(max(text.split('\n'), key=len)) * char_width + left_padding + right_padding, max_width),
                    max_width)
    else:
        width = len(max(text.split('\n'), key=len)) * char_width + left_padding + right_padding

    # Calculate how many characters can fit in one line based on the width
    usable_width = width - left_padding - right_padding
    chars_per_line = usable_width // char_width

    # Split text by newlines to handle multi-paragraph content
    paragraphs = text.split('\n')

    # Initialize total line count
    total_lines = 0

    # Loop through each paragraph and calculate lines per paragraph
    for paragraph in paragraphs:
        total_chars = len(paragraph)
        if total_chars > 0:
            # Calculate how many lines are needed for the current paragraph
            line_count = (total_chars // chars_per_line) + (1 if total_chars % chars_per_line != 0 else 0)
        else:
            # If the paragraph is empty (i.e., consecutive newlines), it's still a line
            line_count = 1

        # Add the number of lines for this paragraph to total line count
        total_lines += line_count

    # Calculate the total height required, which is proportional to the number of lines
    preferred_height = (total_lines * char_height) + top_padding + bottom_padding

    return width, preferred_height


def is_node_flag(node, flag):
    if node.get('id', '').startswith(f'{flag}'):
        return True
    if node['type'] == flag and not node.get('id', '').startswith(f'{BOT_ROLE}'):
        return True
    if node.get('text', '').startswith(f'{flag}:'):
        return True
    return False


def wash_edge_with(edge, _id, _new_id):
    if edge.get('fromNode', '') == _id:
        edge['fromNode'] = _new_id
    if edge.get('toNode', '') == _id:
        edge['toNode'] = _new_id
    return edge


def context_to_message(workdir, block):
    """
    obsidian node , create message object for bot completion
     - Message
     - BotMessage
     - ToolCall
     - ToolCallResult
    """
    block_id = block['id']
    if block_id.startswith(BOT_ROLE) or block['type'] == 'file':
        response_file = block['file']
        message = obsidian_read_bot_response(response_file, workdir)
        return Message(message, BOT_ROLE)
    else:
        message = block['text']
        return Message(message, USER_ROLE)


def generate_uuid(length=16):
    # def length = 32
    uid = str(uuid.uuid4()).replace('-', '')
    if len(uid) > length:
        return uid[:length]
    return uid


def obsidian_chain_to_pya_messages(node_chain, def_prompt, title, working_dir) -> (str, list):
    """
    convert obsidian node chain to pya messages , prompt
    :param node_chain: list of obsidian nodes
    :param def_prompt: fallback prompt
    :param title: title of assistant , and title of target markdown file
    :param working_dir: working directory
    :return: system_prompt, messages
    """
    system_nodes = [node for node in node_chain if is_node_flag(node, 'system')]
    file_ref_nodes = [node for node in node_chain if is_node_flag(node, 'file')]
    other_nodes = [node for node in node_chain if node not in system_nodes and node not in file_ref_nodes]
    print(f'\033[36mChain: message nodes:{len(other_nodes)}, '
          f'\tsys: {len(system_nodes)} , '
          f'\tfiles: {len(file_ref_nodes)}'
          f'\ttotal: {len(node_chain)}\033[0m')
    system_prompt = ''
    # debug view args
    reference_files = []
    if len(system_nodes) > 0:
        for node in system_nodes:
            txt, files = obsidian_read_node(node)
            if len(files) > 0:
                reference_files.extend(files)
            system_prompt += f"{txt}\n"
        system_prompt = system_prompt.strip()
    if not system_prompt:
        if def_prompt and title:
            system_prompt = def_prompt + ", Now you are play with Assistant named " + title
        elif def_prompt:
            system_prompt = def_prompt
        elif title:
            system_prompt = "Now you are play as an friendly personal assistant named " + title
        else:
            system_prompt = ""

    if len(file_ref_nodes) > 0:
        for node in file_ref_nodes:
            _, files = obsidian_read_node(node)
            if len(files) > 0:
                reference_files.extend(files)
    # remove duplicate files
    unique_files = list(set(reference_files))
    if len(unique_files) > 0:
        system_prompt += f"\n\n{len(unique_files)} files attached:\n"
        system_prompt += ''.join([obsidian_read_file(file, working_dir) for file in unique_files])

    return system_prompt, [context_to_message(working_dir, node) for node in other_nodes]


def wash_canvas_node(node, edges, user_color):
    b_id = node['id']
    if '_' not in b_id:
        _new_role_id = f"{USER_ROLE}_{b_id}"
        node['id'] = _new_role_id
        edges = [wash_edge_with(e, b_id, _new_role_id) for e in edges]

    text = str(node['text']).strip().strip('\\')
    node['text'] = text

    # adjust node height to fit text
    # self.adjust_text_area_size(node, text)
    padding = (20, 20, 20, 20)  # top, bottom, left, right
    char_unit_size = (12, 20)
    width = node.get('width', 250)
    if width < 250:
        width = 250
    if width > 1200:
        width = 1200
    test_size = measure_string(text, padding, char_unit_size, fixed_width=width)
    node['width'] = test_size[0]
    node['height'] = test_size[1]

    if user_color and user_color != '0':
        node['color'] = user_color
    return text, edges


def processing_ins_chat_bot(target_bot, node_id, canvas_file, root_dir, edges, nodes, **args):
    # load blank nodes and run processing via bot.
    """
    it means node on canvas file under wdir is a chat node,
    we need to complete the chat node by adding messages to it.
    :param target_bot:
    :param node_id:
    :param canvas_file:
    :param root_dir:
    :param edges:
    :param nodes:
    :param args: extra args
    :return:
    """
    greet_msg = args.get('greet_msg', None)
    if greet_msg:
        print(f'\033[36m{greet_msg}\033[0m')

    ns = [n for n in nodes if n['id'] == node_id]
    node = ns[0]
    target_bot.setup_chat_info(root_dir, canvas_file, node)

    # step 1 , update current node text
    text, edges = target_bot.wash_canvas_node(node, edges)

    # step 2 , create a wink node to link to response node
    target_bot.create_obsidian_elements(node, nodes, edges)

    # step 3 flush
    target_bot.flush_to_obsidian(canvas_file, nodes, edges)

    # read message chain from canvas file.
    target_bot.complete_chat_chains(node, nodes, edges)

    # step 4 , begin chat with bot
    target_bot.bot.chat(text)

    # step 5 , finalize response node
    _method = getattr(target_bot, 'finalize_response_node', None)
    if _method:
        _method()
    else:
        print(' [DONE]')
    pass
