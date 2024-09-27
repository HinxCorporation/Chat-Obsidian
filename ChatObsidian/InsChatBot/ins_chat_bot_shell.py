import json
import os
import threading
import time

from PyAissistant import ChatBot, Chat

from .ins_chat_bot_shell_extend import generate_uuid, wash_canvas_node, obsidian_chain_to_pya_messages, \
    processing_ins_chat_bot, measure_string
from ..obsolete_obsidian_utils import get_relative_file_obsidian, flush_canvas_file, \
    create_response_node, create_node_chain

# define constants for shell
COLOR_PROVIDER = 'color_provider'
DEFAULT_COLOR = '#000'
TARGET_FILE = 'target_file'
ROOT_DIR = 'root_dir'
CANVAS_FILE = 'canvas_file'
NODE = 'node'
LAST_RESPONSE_NODE_ID = 'last_response_node_id'
# use for finalizing response node. for example resize etc..
TITLE = 'title'
BLINK_NODE = 'blink_node'
RESPONSE_NODE_ID = 'response_node_id'


class DelayedTextWriter:
    def __init__(self, target_file, interval=0.5, stack_max=10):
        self.text_stack = ''
        self.interval = interval
        self.stack_max = stack_max
        self.file = target_file
        self.is_alive = True
        self.friendly_goodbye = False
        self.lock = threading.Lock()  # For thread safety
        self.stack_count = 0
        os.makedirs(os.path.dirname(target_file), exist_ok=True)  # Ensure directory exists
        threading.Thread(target=self.life_cycle).start()
        print(f'\033[36m[TextWriter Opened] {target_file} ... \033[0m')

    def life_cycle(self):
        while self.is_alive:
            self.flush()
            time.sleep(self.interval)
            if self.friendly_goodbye:
                self.flush()  # Flush remaining text
                self.is_alive = False
        print('\033[36m[TextWriter Closed]\033[0m')

    def kill(self):
        self.friendly_goodbye = True

    def write(self, text):
        with self.lock:
            self.stack_count += 1
            self.text_stack += text
        if self.stack_count > self.stack_max:
            self.stack_count = 0
            self.flush()  # Flush if stack count exceeds max

    def flush(self):
        with self.lock:
            if len(self.text_stack) == 0:
                return
            with open(self.file, 'a', encoding='utf-8') as flush_char_f:
                flush_char_f.write(self.text_stack)
                self.text_stack = ''
                self.stack_count = 0


class InsChatBotShell:
    def __init__(self, bot: ChatBot, args: dict):
        self.bot = bot
        self.bot._write_out = self.write_out_obsidian
        self.args = args
        self.flush_interval = 0.2
        self.text_writer = None
        self.exclude_first_node = False
        self.append_console_msg = False

    def get(self, key):
        _inside = self.args.get(key, None)
        if not _inside:
            _inside = getattr(self.bot, key, None)
        return _inside

    def set(self, key, value):
        self.args.update({key: value})

    @property
    def title(self):
        _t = self.get(TITLE)
        if not _t and self.bot is not None:
            # test if bot has title attribute
            _t = getattr(self.bot, 'title', None)
        if not _t or _t in ['-', '?']:
            _t = 'Assistant'
        return _t

    @property
    def default_prompt(self):
        _p = self.get('default_prompt')
        if not _p:
            _p = getattr(self.bot, 'default_prompt', None)
        if not _p:
            default_config_file = 'bots/obsidian_bot.txt'
            if os.path.exists(default_config_file):
                with open(default_config_file, 'r', encoding='utf-8') as f:
                    _p = f.read().strip()
        if not _p:
            _p = """As an AI chatbot in Obsidian, your job is to assist the user by generating responses directly 
            onto the canvas. Keep it straightforward, helpful, and organized."""
        return _p

    def complete_chat_to_pya_message(self, node_chain):
        fall_back_prompt = self.default_prompt
        system_prompt, messages = obsidian_chain_to_pya_messages(
            node_chain,
            fall_back_prompt,
            self.title,
            self.get(ROOT_DIR))
        # bot_prompt = getattr(self.bot, 'prompt', None) print('\033[36m' + f'Bot: {bot_prompt}, \n\nFallback: {
        # fall_back_prompt[:100]}\n\nSystem: {system_prompt[:100]}\n' + '\033[0m') if bot_prompt: # maybe duplicate
        # prompt, check if it's already in system prompt if bot_prompt in system_prompt: pass else: system_prompt =
        # bot_prompt + '/n' + system_prompt
        self.bot.current_chat.system_prompt = system_prompt
        return messages

    def get_color(self, tag):

        provider = self.get(COLOR_PROVIDER)
        try:
            if provider:
                return provider(tag)
        except:
            pass
        return False, DEFAULT_COLOR

    def write_out_obsidian(self, word):
        self.text_writer.write(word)
        if self.append_console_msg:
            print(word, end='')

    def setup_chat_info(self, root_dir, canvas_file, node):
        self.set(ROOT_DIR, root_dir)
        self.set(CANVAS_FILE, canvas_file)
        self.set(NODE, node)
        self.set(RESPONSE_NODE_ID, generate_uuid(32))
        # self.args.update({ROOT_DIR: root_dir, CANVAS_FILE: canvas_file, NODE: node})

    def wash_canvas_node(self, node, edges):
        color_str = None
        y_user, user_color = self.get_color('user_dialog')
        if y_user and user_color != '0':
            color_str = user_color
        return wash_canvas_node(node, edges, color_str)

    def get_current_append_file(self, create_type=''):
        _canvas_file = self.get(CANVAS_FILE)  # current canvas file
        _response_id = self.get(RESPONSE_NODE_ID)  # current_response_id
        _title = self.title
        canvas_folder, canvasName = os.path.split(_canvas_file)
        full_path = os.path.join(canvas_folder,
                                 f'dialog/{canvasName}.ai.assets',
                                 _response_id,
                                 f'{_title}{create_type}.md')
        return os.path.abspath(str(full_path)).replace('\\', '/')

    def flush_to_obsidian(self, canvas_file, nodes, edges):
        y_system, system_color = self.get_color('system_dialog')
        flush_canvas_file(canvas_file, nodes, edges, y_system, system_color)

    def complete_chat_chains(self, node, nodes, edges):
        node_chain = create_node_chain(node, nodes, edges)
        if node_chain is not None and len(node_chain) > 0:
            if self.exclude_first_node:
                node_chain = node_chain[1:]
        self.complete_chat_with_chains(node_chain)

    def complete_chat_with_chains(self, node_chain):
        self.bot.current_chat = Chat()
        self.bot.current_chat.messages.extend(self.complete_chat_to_pya_message(node_chain))

    def finalize_response_node(self):
        try:
            self.text_writer.kill()
            n_id = self.get(LAST_RESPONSE_NODE_ID)
            if n_id:
                current_canvas_file = self.get(CANVAS_FILE)
                with open(current_canvas_file, 'r', encoding='utf-8') as f:
                    json_dat = json.load(f)
                    nodes = json_dat['nodes']
                    edges = json_dat['edges']

                node = next((n for n in nodes if n['id'] == n_id), None)
                if not node:
                    return  # Exit if no node matches the id
                # new_wid = 880
                # new_hei = 600
                current_width = node.get('width')
                current_height = node.get('height')
                if current_width != 880 or current_height != 600:
                    return  # user has already resized the node.
                text = self.bot.current_chat.messages[-1].content
                padding = (70, 20, 20, 20)  # top, bottom, left, right ; title extra 52 pixels
                test_size = measure_string(text, padding, (12, 20), fixed_width=current_width)
                current_height = node.get('height', 100)
                times = 1.2
                if test_size[1] * times < current_height:
                    node['height'] = test_size[1]
                    flush_canvas_file(current_canvas_file, nodes, edges, False, "3")
        except:
            pass

    def create_obsidian_elements(self, node, nodes, edges):
        target_file = self.get_current_append_file()
        self.set(TARGET_FILE, target_file)
        self.text_writer = DelayedTextWriter(target_file, self.flush_interval)
        working_dir = self.get(ROOT_DIR)
        rel_file = get_relative_file_obsidian(target_file, working_dir)
        _, color_str = self.get_color('assistant_dialog')
        new_node, new_trans = create_response_node(node, rel_file, color_str)
        self.set(LAST_RESPONSE_NODE_ID, new_node['id'])
        nodes.append(new_node)
        edges.append(new_trans)
        self.set(BLINK_NODE, new_node)

    def processing(self, node_id, canvas_file, root_dir, edges, nodes, **args):
        """
        fire up processing canvas node with bot.
        :param node_id: current node id
        :param canvas_file: current canvas file
        :param root_dir: root directory of obsidian
        :param edges: current edges
        :param nodes: current nodes
        :param args: [ title, custom_title, prompt, custom_prompt, default_prompt ]
        """

        # read title or custom title from args
        _title = args.get(TITLE)
        if not _title:
            _title = args.get('custom_' + TITLE)
        if _title:
            self.set(TITLE, _title)

        # read prompt or custom prompt from args
        _prompt = args.get('prompt')
        if not _prompt:
            _prompt = args.get('custom_prompt')
        if _prompt:
            # print('\033[36m' + f'Prompt: {_prompt}' + '\033[0m')
            self.set('default_prompt', _prompt)
        else:
            # print('\033[36m' + f'Prompt is empty, default now is {self.get("default_prompt")}' + '\033[0m')
            pass

        self.bot._write_out = self.write_out_obsidian
        processing_ins_chat_bot(self, node_id, canvas_file, root_dir, edges, nodes, **args)
