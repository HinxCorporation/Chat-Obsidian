import os
import threading

from PyAissistant import Chat

from ChatObsidian import create_node_chain, InsCustom
from Workflow import FlowData
from Workflow import Monitor
from Workflow import Step
from .obsidian_bot_utils import construct_bot
from ..chat_obsidian import ChatUtil, load_blank_nodes_from_canvas_file


class _chat_prepare_bot_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # monitor.log('File processing started with canvas file.')
        pass


class _chat_process_node_chain_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # calculate and wash the node chain
        canvas_file = data.get('file')
        goes_to_chat, nodes, edges = load_blank_nodes_from_canvas_file(canvas_file)
        # monitor.log('Canvas file calculate finished.')
        data.set('goes_to_chat', goes_to_chat)
        data.set('nodes', nodes)
        data.set('edges', edges)


class _process_messages_step(Step):

    def __init__(self, name: str, is_critical: bool = False):
        super().__init__(name, is_critical)
        self.data = None
        self.monitor = None

    def _custom_flow_continue(self):
        pass

    def _test_custom_bot(self, node):
        node_type = node.get('type')
        if node_type == 'text':
            text = node.get('text').strip()
            # process if @bot_name
            if text.startswith('@'):
                return True, text[1:]
            # process if /bot_name
            elif text.startswith('/'):
                return True, text[1:]
            # process if bot:bot_name
            elif text.startswith('bot:'):
                return True, text[4:]
            return False, ''
        elif node_type == 'file':
            file = node.get('file')
            wdir = self.data.get('note_root')
            preserve_file = str(os.path.join(wdir, file).replace('\\', '/'))
            preserve_file = os.path.abspath(preserve_file)
            if os.path.exists(preserve_file):
                _, filename = os.path.split(preserve_file)
                # if name starts with bot_
                if filename.startswith('bot_'):
                    return True, f'file:{preserve_file}'
        return False, ''

    def _create_chat_bot(self, opt: str, sel: bool, **kwargs):
        if not sel or not opt:
            return ChatUtil.__CREATE_BOT__(**kwargs)
        else:
            opt = opt.strip()
            su, bot = construct_bot(opt, program=self)
            if su:
                return bot
            if bot is not None:
                self.monitor.error(f"Instance was created but not detected. Option: {opt}.")
            self.monitor.error(f"Failed to create chat bot with option {opt}.")
            return ChatUtil.__CREATE_BOT__(**kwargs)

    def _continue_with_bot(self, bot, node, canvas_file, skip_1=True):
        data = self.data
        ins_custom = InsCustom(bot)
        if skip_1:
            ins_custom.exclude_first_node = True
        # requires node_id, canvas_files,root_dir,edges,nodes,**args
        edges = data.get('edges')
        nodes = data.get('nodes')

        run_args = {
            'node_id': node['id'],
            'canvas_file': canvas_file,
            'root_dir': data.get('note_root'),
            'edges': edges,
            'nodes': nodes,
        }
        _title = node.get('title')
        if not _title:
            _title = node.get('name')
        if _title:
            run_args['title'] = _title
        _prompt = node.get('prompt')
        if _prompt:
            run_args['prompt'] = _prompt

        self.monitor.log(f"Obsidian will complete at background.")
        threading.Thread(target=lambda: ins_custom.processing(**run_args)).start()

    def __continue_with_obsidian_bot(self, node, monitor, data, canvas_file, exclude_first_node=False):
        """
        continue with InsChatBot
        """
        nodes = data.get('nodes')
        edges = data.get('edges')
        wdir = data.get('note_root')
        util = data.get('util')
        bot = ChatUtil.__CREATE_BOT__(util.get_color)

        monitor.log('Blank node found. Will start chat.')
        # prepare chat bot and set up the environment
        bot.setup_chat_info(wdir, canvas_file, node)
        # wash canvas node, current node change to chat node, and wash edges with the old node id.
        text, edges = bot.wash_canvas_node(node, edges)
        # setup write to , and create bot link node elements. join to the canvas file
        bot.create_obsidian_elements(node, nodes, edges)
        # flush the new datas to the canvas file
        bot.flush_to_obsidian(canvas_file, nodes, edges)
        _chain = create_node_chain(node, nodes, edges)
        if exclude_first_node:
            _chain = _chain[1:]
        # processing message chain
        msg_text = text

        if data.get('_use_built_in_chains', False):
            monitor.warning('Using built-in chains')
            bot.complete_chat_chains(node, nodes, edges)
            bot.complete_chat_with_chains(_chain)
        else:
            monitor.log('Using advanced chains to complete chat message chain')
            chain_flow = data.get('chain_flow')
            _new_chat = Chat()
            # exclude Current, get previous chain and append to new chat

            payload = {
                'chain': _chain,
                'wdir': wdir,
                'bot': bot
            }
            monitor.log(f"Running chain flow with length {(len(_chain))} ,root = {wdir}")
            result = chain_flow.run(payload, f"Processing chain with :{node['id']}")
            if result.get('error'):
                monitor.error(
                    f"Error processing chat with {node['name']}. Error: {result.get('error')}")
            else:
                _new_chat.messages = result.get('messages')
                _new_prompt = result.get('prompt', '')
                _new_title = result.get('title', '')
                if not _new_title:
                    _new_title = result.get('subject', '')
                _custom_model = result.get('custom_model', '')
                if not _custom_model:
                    _custom_model = result.get('model', '')
                _context = result.get('context', '')

                # this may not import to a chat completion, the most import is messages.
                if _new_prompt:
                    _new_chat.system_prompt = _new_prompt
                if _new_title:
                    _new_chat.title = _new_title
                if _custom_model:
                    _new_chat.model = _custom_model
                if _context:
                    _new_chat.context = _context

                bot.current_chat = _new_chat
            util = result.get('util')
            msg = util.node_to_message(node)
            msg_text = msg.content

        # start chat
        monitor.info(f'Start chat send: {msg_text}')
        self.start_up_chat_thread(bot, msg_text)
        monitor.info(f"Chat started. Chat will complete in Obsidian. at background.")

    def _continue_with(self, node, monitor, data, canvas_file):
        nodes = data.get('nodes')
        edges = data.get('edges')

        _chain = create_node_chain(node, nodes, edges)
        custom_bot_opt = ''
        custom_bot_sel = False
        if _chain is not None and len(_chain) > 0:
            first_node = _chain[0]
            custom_bot_sel, custom_bot_opt = self._test_custom_bot(first_node)

        if not custom_bot_sel:
            self.__continue_with_obsidian_bot(node, monitor, data, canvas_file)
        else:
            bot = self._create_chat_bot(custom_bot_opt, custom_bot_sel)
            if bot is None:
                self.__continue_with_obsidian_bot(node, monitor, data, canvas_file, True)
            else:
                self._continue_with_bot(bot, node, canvas_file)

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        self.data = data
        self.monitor = monitor
        # process node chain to messages
        goes_to_chat = data.get('goes_to_chat')
        canvas_file = data.get('file')
        nodes = data.get('nodes')
        edges = data.get('edges')
        wdir = data.get('note_root')
        util = data.get('util')
        i_len = len(goes_to_chat)
        if i_len > 0:
            for blank_node in goes_to_chat:
                monitor.log('Meet blank node with , gos to chat.')
                if not data.get('easy_mode', False):
                    # --------------------------CUSTOM PIPELINE BUILD CHAT---------------------------
                    node_id = blank_node['id']
                    ns = [n for n in nodes if n['id'] == node_id]
                    if len(ns) > 0:
                        node = ns[0]
                        self._continue_with(node, monitor, data, canvas_file)
                    else:
                        monitor.error(f"Node with id {node_id} not found in nodes list.")
                    # -----------------------------------------------------
                else:
                    # --------------------------EASY MODE CHAT (NO PIPELINE)---------------------------
                    monitor.log(f"Easy mode is on. Chat will work and complete in Obsidian. at background.")
                    # threading.Thread(target=lambda:
                    # bot.complete_obsidian_chat(blank_node['id'], canvas_file, nodes, edges,wdir)).start()
                    args = {blank_node['id'], canvas_file, nodes, edges, wdir}
                    threading.Thread(
                        target=lambda: ChatUtil.__CREATE_BOT__(util.get_color).complete_obsidian_chat(*args)).start()
        else:
            pass

    def start_up_chat_thread(self, bot, message_text):
        # get text from node , and
        threading.Thread(target=lambda: self.start_up_chat_thread_entry(bot, message_text)).start()
        pass

    @staticmethod
    def start_up_chat_thread_entry(bot, message_text):
        bot.chat(message_text)
        print(' [DONE]')
        bot.finalized_canvas_dialog()


class _chat_finalize_bot_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # finalize the bot and make chat
        pass


class _chat_complete_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # self loop to complete the chat
        pass


class _chat_after_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # grace and cleanup
        pass
