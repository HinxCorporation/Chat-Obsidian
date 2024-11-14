import os
import threading
import time

from ChatObsidian.obsolete_obsidian_utils.obsidian_utils import create_node_chain
from ChatObsidian import InsCustom
from Workflow import FlowData
from Workflow import Monitor
from Workflow import Step
from .obsidian_bot_utils import construct_bot
from .processors import flow_0, flow_1, flow_2
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

        self.flow_0 = flow_0.create()
        self.flow_0_requires = ['node', 'nodes', 'edges', 'file', 'note_root', 'util',
                                'exclude_first_node', 'chain_flow', '_use_built_in_chains']
        self.flow_0.preview()

        self.flow_1 = flow_1.create()
        self.flow_1_requires = ['node', 'file', 'ins_custom', 'edges', 'nodes', 'note_root']
        self.flow_1.preview()

        self.flow_2 = flow_2.create()
        self.flow_2_requires = ['node', 'file', 'ins_custom', 'edges', 'nodes', 'note_root']
        self.flow_2.preview()

    def _custom_flow_continue(self):
        pass

    def _test_custom_bot(self, node):
        """
        if @bot /bot or bot:bot_name in node text, return True and bot_name
        elif linked file starts with bot_ return True and file path
        else return False and ''
        """
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

    def _create_chat_bot(self, opt: str, select_from_opt: bool = True, **kwargs):
        """
        Create a bot from engine.
        """
        if not select_from_opt or not opt:
            return ChatUtil.__CREATE_BOT__(**kwargs), dict()
        else:
            opt = opt.strip()
            su, bot, conf = construct_bot(opt, program=self)
            if su:
                return bot, conf
            if bot is not None:
                self.monitor.error(f"Instance was created but not detected. Option: {opt}.")
            self.monitor.error(f"Failed to create chat bot with option {opt}.")
            return ChatUtil.__CREATE_BOT__(**kwargs), dict()

    def _continue_with_bot(self, bot, node, monitor, canvas_file, skip_1=True):
        """
        Continue with custom bot (create from dialog option)
        """
        data = self.data
        copied_data = dict()
        ins_custom = InsCustom(bot)
        copied_data['ins_custom'] = ins_custom
        copied_data['node'] = node
        copied_data['file'] = canvas_file
        copied_data['note_root'] = data.get('note_root')
        # copied_data['monitor'] = monitor
        if skip_1:
            ins_custom.exclude_first_node = True
        for k in self.flow_1_requires:
            if k not in copied_data:
                if data.has(k):
                    copied_data[k] = data.get(k)
                else:
                    # monitor.error(f"Data key {k} is missing.")
                    time.sleep(1)
                    return
        additional_data = self.data.get('advance_config', dict())
        if additional_data:
            try:
                # ins_custom.set_config(additional_data)
                ins_config = additional_data.get('InsBot', None)
                if ins_config is None:
                    pass
                else:
                    monitor.log(f"Setting advance config for ins bot shell.")
                    e, s, i = ins_custom.apply_additional_settings(ins_config)
                    if len(e) > 0:
                        for err in e:
                            monitor.error(f"Error in ins config: {err}")
                    if len(i) > 0:
                        monitor.warning(f"Ignored ins config: {i}")
                pass
            except:
                monitor.error(f"Failed to set advance config {additional_data}.")
                pass
        if skip_1:
            self.flow_1.run(copied_data, "processing chat with custom bot", custom_monitor=monitor)
        else:
            self.flow_2.run(copied_data, "processing chat with custom bot [SPE COMPLEX]", custom_monitor=monitor)

    def __continue_with_obsidian_bot(self, node, monitor, data, canvas_file, exclude_first_node=False):
        """
        continue with InsChatBot (default options)
        """
        data.set('exclude_first_node', exclude_first_node)
        data.set('node', node)
        data.set('file', canvas_file)
        for k in self.flow_0_requires:
            if not data.has(k):
                monitor.error(f"Data key {k} is missing.")
                time.sleep(1)
                return
        # copy data and start flow 0
        copied_data = dict()
        for k in self.flow_0_requires:
            copied_data[k] = data.get(k)
        self.flow_0.run(copied_data, "processing chat with default obsidian bot", custom_monitor=monitor)

    def _continue_with(self, node, monitor, data, canvas_file):
        nodes = data.get('nodes')
        edges = data.get('edges')

        _chain = create_node_chain(node, nodes, edges)

        if _chain is not None and len(_chain) > 0:
            first_node = _chain[0]
        else:
            first_node = node
        custom_bot_sel, custom_bot_opt = self._test_custom_bot(first_node)

        bot = None
        skip_1 = True
        if custom_bot_sel:
            custom_bot_opt = custom_bot_opt.strip()
            known_spliter = [' ', '\t', ', ']
            for spliter in known_spliter:
                if spliter in custom_bot_opt:
                    custom_bot_opt = custom_bot_opt.split(spliter)[0]
                    skip_1 = False
                    break
            bot, advance_config = self._create_chat_bot(custom_bot_opt, custom_bot_sel)
            if advance_config:
                data.set('advance_config', advance_config)
        else:
            monitor.warning('No custom bot selected. This will be obsolete in the future. Please use as Obsidian bot.')

        # going to processing
        if not custom_bot_sel or bot is None:
            # still a fallback to obsidian bot
            self.__continue_with_obsidian_bot(node, monitor, data, canvas_file)
            monitor.warning('Processing with flow 0 (obsidian bot)')
        else:
            if skip_1:
                monitor.log('Processing with flow 1 (custom bot)')
            else:
                monitor.log('Processing with flow 2 (custom bot [SPE COMPLEX])')
            # continue with custom bot weather skip it or not , there already exist a chat bot
            self._continue_with_bot(bot, node, monitor, canvas_file, skip_1)

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
