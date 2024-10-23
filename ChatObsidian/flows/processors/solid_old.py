import threading

from PyAissistant import Chat

from ChatObsidian.chat_obsidian import ChatUtil
from ChatObsidian.obsolete_obsidian_utils.obsidian_utils import create_node_chain as create_node_chain_by_util
from Workflow import WorkflowBuilder, Step, FlowData, Monitor


class ex_processing_flow:

    @staticmethod
    def create():
        """
        ensure you do have elements named [ 'bot', 'node', 'nodes', 'edges', 'file', 'note_root',
         'exclude_first_node', 'chain_flow', '_use_built_in_chains' ]
        """
        return (
            WorkflowBuilder()
            .add_step(process_pre_data("1. Process Pre-Data", is_critical=True))
            .add_step(setup_chat_info("2. Setup Chat Info", is_critical=True))
            .add_step(wash_canvas_node("3. Wash Canvas Node", is_critical=True))
            .add_step(create_obsidian_elements("4. Create(Update) Obsidian Elements", is_critical=True))
            .add_step(flush_obsidian_elements("5. Flush Obsidian Elements", is_critical=True))
            .add_step(create_node_chain("6. Create Node Chain", is_critical=True))
            .add_step(node_chain_to_messages("7. Node Chain to Messages", is_critical=True))
            .add_step(processing_chat("8. Processing Chat", is_critical=True))
            .add_step(finished_chat("9. Finished Chat", is_critical=True))
            .build()
        )


class process_pre_data(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        util = data.get('util')
        bot = ChatUtil.__CREATE_BOT__(util.get_color)
        data.set('bot', bot)
        pass


class setup_chat_info(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot = data.get('bot')
        wdir = data.get('note_root')
        monitor.log('Loading note and canvas file')
        node = data.get('node')
        canvas_file = data.get('file')
        monitor.log('Blank node found. Will start chat.')
        # prepare chat bot and set up the environment
        bot.setup_chat_info(wdir, canvas_file, node)
        pass


class wash_canvas_node(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        # wash canvas node, current node change to chat node, and wash edges with the old node id.
        bot = data.get('bot')
        node = data.get('node')
        edges = data.get('edges')
        text, edges = bot.wash_canvas_node(node, edges)
        data.set('text', text)
        data.set('edges', edges)


class create_obsidian_elements(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot = data.get('bot')
        node = data.get('node')
        nodes = data.get('nodes')
        edges = data.get('edges')
        # setup write to , and create bot link node elements. join to the canvas file
        bot.create_obsidian_elements(node, nodes, edges)
        pass


class flush_obsidian_elements(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot = data.get('bot')
        canvas_file = data.get('file')
        nodes = data.get('nodes')
        edges = data.get('edges')
        # flush the new datas to the canvas file
        bot.flush_to_obsidian(canvas_file, nodes, edges)
        pass


class create_node_chain(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        node = data.get('node')
        nodes = data.get('nodes')
        edges = data.get('edges')

        exclude_first_node = data.get('exclude_first_node')
        _chain = create_node_chain_by_util(node, nodes, edges)
        if exclude_first_node:
            _chain = _chain[1:]
        data.set('node_chain', _chain)
        pass


class node_chain_to_messages(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        pass


class processing_chat(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        bot = data.get('bot')
        node = data.get('node')
        nodes = data.get('nodes')
        edges = data.get('edges')
        _chain = data.get('node_chain')
        wdir = data.get('note_root')

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
            data.set('msg_text', msg_text)
        pass


class finished_chat(Step):

    @staticmethod
    def start_up_chat_thread_entry(bot, message_text):
        print('Starting up chat thread...')
        bot.chat(message_text)
        print(' [DONE]')
        bot.finalized_canvas_dialog()

    def start_up_chat_thread(self, bot, message_text):
        # get text from node , and
        threading.Thread(target=lambda: self.start_up_chat_thread_entry(bot, message_text)).start()
        pass

    def execute(self, data: FlowData, monitor: Monitor):
        msg_text = data.get('msg_text')
        bot = data.get('bot')
        # start chat
        monitor.info(f'Start chat send: {msg_text}')
        self.start_up_chat_thread(bot, msg_text)
        monitor.info(f"Chat started. Chat will complete in Obsidian. at background.")
        pass

# #################################THE ORIGINAL DOC OF PYTHON###############################################
# nodes = data.get('nodes')
# edges = data.get('edges')
# wdir = data.get('note_root')
# util = data.get('util')
# bot = ChatUtil.__CREATE_BOT__(util.get_color)
#
# monitor.log('Blank node found. Will start chat.')
# # prepare chat bot and set up the environment
# bot.setup_chat_info(wdir, canvas_file, node)
# # wash canvas node, current node change to chat node, and wash edges with the old node id.
# text, edges = bot.wash_canvas_node(node, edges)
# # setup write to , and create bot link node elements. join to the canvas file
# bot.create_obsidian_elements(node, nodes, edges)
# # flush the new datas to the canvas file
# bot.flush_to_obsidian(canvas_file, nodes, edges)
# _chain = create_node_chain(node, nodes, edges)
# if exclude_first_node:
#     _chain = _chain[1:]
# # processing message chain
# msg_text = text
#
# if data.get('_use_built_in_chains', False):
#     monitor.warning('Using built-in chains')
#     bot.complete_chat_chains(node, nodes, edges)
#     bot.complete_chat_with_chains(_chain)
# else:
#     monitor.log('Using advanced chains to complete chat message chain')
#     chain_flow = data.get('chain_flow')
#     _new_chat = Chat()
#     # exclude Current, get previous chain and append to new chat
#
#     payload = {
#         'chain': _chain,
#         'wdir': wdir,
#         'bot': bot
#     }
#     monitor.log(f"Running chain flow with length {(len(_chain))} ,root = {wdir}")
#     result = chain_flow.run(payload, f"Processing chain with :{node['id']}")
#     if result.get('error'):
#         monitor.error(
#             f"Error processing chat with {node['name']}. Error: {result.get('error')}")
#     else:
#         _new_chat.messages = result.get('messages')
#         _new_prompt = result.get('prompt', '')
#         _new_title = result.get('title', '')
#         if not _new_title:
#             _new_title = result.get('subject', '')
#         _custom_model = result.get('custom_model', '')
#         if not _custom_model:
#             _custom_model = result.get('model', '')
#         _context = result.get('context', '')
#
#         # this may not import to a chat completion, the most import is messages.
#         if _new_prompt:
#             _new_chat.system_prompt = _new_prompt
#         if _new_title:
#             _new_chat.title = _new_title
#         if _custom_model:
#             _new_chat.model = _custom_model
#         if _context:
#             _new_chat.context = _context
#
#         bot.current_chat = _new_chat
#     util = result.get('util')
#     msg = util.node_to_message(node)
#     msg_text = msg.content
#
# # start chat
# monitor.info(f'Start chat send: {msg_text}')
# self.start_up_chat_thread(bot, msg_text)
# monitor.info(f"Chat started. Chat will complete in Obsidian. at background.")
