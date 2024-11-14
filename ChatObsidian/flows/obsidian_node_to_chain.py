import os
import re
import time

import requests
from PyAissistant import Message

from ChatObsidian.obsolete_obsidian_utils.obsidian_utils import obsidian_read_file
from Workflow import Step, WorkflowBuilder, FlowData, Monitor, Workflow


class utils:

    def __init__(self):
        self.files = []
        self.wdir = ''

    def read_system_node(self, node, monitor):
        # returns context, ats, attachments
        # type is system, so its id starts with system or text starts with system:
        node_type = node.get('type', '')
        text = ''
        if node_type == 'text':
            text = node.get('text', '')
            text = text.replace('system:', '').strip()
        elif node_type == 'file':
            refer_file = node.get('file', '')
            text = self.__read_obsidian_reference(refer_file)
        else:
            pass

        if text:
            # read @xxx and [[xxx]] from text, via regex
            text = self.wash_markdown_statement(text)
            return text, [], []
        monitor.error(f"Unknown system node type: {node_type}")
        return '', [], []

    @staticmethod
    def is_node_with_flag(node, flag):
        if node.get('id', '').startswith(f'{flag}'):
            return True
        # not assistant and type is flag
        if node['type'] == flag and not node.get('id', '').startswith(f'assistant'):
            return True
        if node.get('text', '').startswith(f'{flag}:'):
            return True
        return False

    def __read_obsidian_reference(self, file):
        # read item and return its content
        target_file = None
        if os.path.exists(file):
            target_file = file
        if not target_file:
            # find files under wdir_files and match the best on for target_file
            target_file = self.query_file_in_obsidian_files(file)
        if target_file:
            print('\033[32m' + f"Read file: {target_file}" + '\033[0m')
            with open(target_file, 'r', encoding='utf-8') as f:
                return f.read()
        return f'{file} not exist'

    def read_obsidian_reference(self, file):
        return self.__read_obsidian_reference(file)

    def query_file_in_obsidian_files(self, query):
        is_extension_include = False
        # normalize query
        query = query.replace('\\', '/')
        _, filename = os.path.split(query)

        if '.' in filename:
            is_extension_include = True
        if not is_extension_include:
            with_ext = query + '.md'
            guess_file = os.path.join(self.wdir, with_ext).replace('\\', '/')
        else:
            guess_file = os.path.join(self.wdir, query).replace('\\', '/')
        if os.path.exists(guess_file):
            return os.path.abspath(guess_file).replace('\\', '/')

        if len(self.files) == 0:
            print('\033[31m' + f'Unable to match file, go collect, :{query}' + '\033[0m')
            self._self_require_files()

        files = self.files
        if is_extension_include:
            for record in files:
                if record.endswith(query):
                    return record
        else:
            for record in files:
                _basename, _ = os.path.splitext(record)
                # must end with the query will match the file.
                if _basename.endswith(query):
                    return record
        return ''

    def node_to_message(self, block):
        block_id = block['id']
        if block_id.startswith('assistant') or block['type'] == 'file':
            response_file = block['file']
            message = self.__read_obsidian_reference(response_file)
            return Message(message, 'assistant')
        else:
            message = self.wash_markdown_statement(block['text'])
            return Message(message, 'user')

    def __collect_obsidian_files_under(self, wdir=''):
        if not wdir:
            wdir = self.wdir
        if not wdir:
            print('\033[31m' + 'Warning: wdir not set, no obsidian files collected.' + '\033[0m')
            return []
        if not os.path.exists(wdir):
            return []
        if os.path.isfile(wdir):
            ends = os.path.splitext(wdir)[1]
            if ends in ['.md', '.txt', '.html', '.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.json', '.yaml', '.yml']:
                return [wdir]
            return []
        files = []
        if os.path.isdir(wdir):
            for entry in os.scandir(wdir):
                _path = entry.path
                # if entry.is_dir and _path.endswith('.ai.assets'):
                #     continue
                files.extend(self.__collect_obsidian_files_under(_path))
        return files

    @staticmethod
    def get_at_statement(target):
        return f"`at {target}`"

    def get_doc_statement(self, doc):
        return self.__read_obsidian_reference(doc)

    def get_link_statement(self, title, url):
        try:
            url = url.strip("'").strip('"').strip()
            if url.startswith('http'):
                response = requests.get(url, proxies={"http": '', "https": ''})
                if response.status_code == 200:
                    context = response.text
                else:
                    context = f"Error: {response.status_code}"
            else:
                context = self.__read_obsidian_reference(url)
        except Exception as e:
            context = f"Error: {e}"
            pass
        return f"`web:{title} - ({url}) `\n~~~html\n{context}\n~~~"

    def re_parse_markdown_statement(self, match):
        at_match = match.group('at')
        doc_match = match.group('doc')
        link_match = match.group('link_text')
        url_match = match.group('url')
        if at_match:
            return utils.get_at_statement(at_match)
        elif doc_match:
            return self.get_doc_statement(doc_match)
        elif link_match and url_match:
            return self.get_link_statement(link_match, url_match)
        return match.group(0)

    def wash_markdown_statement(self, text):
        combined_pattern = re.compile(
            r'@(?P<at>\w+)\b|'  # Match @username (followed by any non-word boundary)
            r'\[\[(?P<doc>.*?)\]\]|'  # Match [[doc_key]]
            r'\[(?P<link_text>.*?)\]\((?P<url>.*?)\)'  # Match [link_text](url)
        )
        return combined_pattern.sub(self.re_parse_markdown_statement, text)

    def init_files(self, wdir):
        self.wdir = wdir
        # here is not needs to collect it , because it may always be collected in the previous step if it needs.
        pass

    def _self_require_files(self):
        self.files = self.__collect_obsidian_files_under()
        self.files = [os.path.abspath(file).replace('\\', '/') for file in self.files]


__all__ = ['utils', 'create_flow']


def create_flow() -> Workflow:
    """
    These steps focus on processing obsidian node to chat message.
    node is a json payload,
    message is PyAissistant.Message ; message able to parse to request payload via its.message_dict()

    # essential input : chain,wdir
    # optional input : title

    # essential output : messages, prompt
    # optional output : title or subject, custom_model or model, context
    # --------------------------------------
    """

    # traditional setting, sys node is the first node in the chain.
    # if there is no sys node, append system prompt ad first
    # if there are several sys nodes, append system prompt after the last sys node.

    return (
        WorkflowBuilder()
        .add_step(_obsidian_node_to_chain_init("OBS-Chain-01-Init"))
        .add_step(_obsidian_node_processing_prompt("OBS-Chain-02-System-Prompt"))
        .add_step(_obsidian_node_chain_to("OBS-Chain-03-Chain-To-Messages"))
        .build())


# Step 01
class _obsidian_node_to_chain_init(Step):

    def execute(self, data: FlowData, monitor: Monitor):
        # ensure there is wdir and chain and chain is list or array
        chain = data.get('chain')
        if not chain or not isinstance(chain, list):
            monitor.error('chain is not set or not a list')
        wdir = data.get('wdir')
        if not wdir:
            monitor.error('wdir is not set')
        util = utils()
        time_now = time.time()
        util.init_files(wdir)
        time_span = time.time() - time_now
        print(f"Obsidian files collected in {time_span:.2f} seconds.")
        data.set('util', util)
        pass


# Step 02
class _obsidian_node_processing_prompt(Step):

    @staticmethod
    def get_default_prompt(title):
        sys_prompt = ("As an AI chatbot in Obsidian, your job is to assist the user by generating responses "
                      "directly onto the canvas. Keep it straightforward, helpful, and organized.If there is "
                      "a complex task, finished it step by step.")
        if title:
            sys_prompt = sys_prompt + ", Now you are play with Assistant named " + title
        return sys_prompt

    @staticmethod
    def complete_obsidian_prompt(data, monitor):
        files = data.get('util')
        util = data.get('util')

        chain = data.get('chain')
        total = len(chain)
        wdir = data.get('wdir')
        sys_prompt = ''
        position = 0
        is_sys_node_process = False
        system_ats = []
        system_attachments = []

        while position < total:
            node = chain[position]
            if utils.is_node_with_flag(node, 'system'):
                is_sys_node_process = True
                _context, ats, attaches = util.read_system_node(node, monitor)
                position += 1
                if ats is not None and len(ats) > 0:
                    system_ats.extend(ats)
                if attaches is not None and len(attaches) > 0:
                    system_attachments.extend(attaches)
                _context = _context.strip()
                if _context:
                    if sys_prompt:
                        sys_prompt = f"{sys_prompt}\n{_context}"
                    else:
                        sys_prompt = _context
            else:
                break
        blank_prompt = not is_sys_node_process or not sys_prompt
        if blank_prompt:
            title = data.get('title', '')
            sys_prompt = _obsidian_node_processing_prompt.get_default_prompt(title)

        if system_ats is not None and len(system_ats) > 0:
            sys_prompt += f"\nHere is special at target:\n"
            sys_prompt += ",".join([util.get_at_statement(at) for at in system_ats])

        if system_attachments is not None and len(system_attachments) > 0:
            sys_prompt += f"\n\n{len(system_attachments)} files attached:\n"

            if data.get('use_built_in_obsidian_reader'):
                sys_prompt += '\n'.join([obsidian_read_file(file, wdir) for file in system_attachments])
            else:
                sys_prompt += '\n'.join([util.read_obsidian_reference(file) for file in system_attachments])

        data.set('prompt', sys_prompt)
        return position

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        chain = data.get('chain')
        total = len(chain)

        if total == 0:
            title = data.get('title', '')
            data.set('prompt', self.get_default_prompt(title))
        else:
            position = self.complete_obsidian_prompt(data, monitor)
            data.set('position', position)
        pass


# step 03
class _obsidian_node_chain_to(Step):

    def execute(self, data: FlowData, monitor: Monitor):
        util = data.get('util')
        chain = data.get('chain')
        total = len(chain)

        messages = []
        if total > 0:
            position = data.get('position', 0)
            while position < total:
                node = chain[position]
                # process
                messages.append(util.node_to_message(node))
                position += 1

        data.set('messages', messages)
        pass
