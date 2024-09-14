import configparser
import os
import threading
import time

from ChatObsidian.ObsidianShared import current
from ChatObsidian.WatcherUtil import initialize_with_config, setup_observers
from ChatObsidian.obsolete_obsidian_utils.chatutil import ChatUtil, load_blank_nodes_from_canvas_file
from Workflow import FlowData
from Workflow import Monitor
from Workflow import Step
from Workflow import WorkflowBuilder


class _chat_prepare_bot_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # make a bot and get ready
        pass


class _chat_process_node_chain_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # calculate and wash the node chain
        canvas_file = data.get('file')
        goes_to_chat, nodes, edges = load_blank_nodes_from_canvas_file(canvas_file)

        data.set('goes_to_chat', goes_to_chat)
        data.set('nodes', nodes)
        data.set('edges', edges)


class _process_messages_step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
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
                bot = ChatUtil.__CREATE_BOT__(util.get_color)
                args = {blank_node['id'], canvas_file, nodes, edges, wdir}
                # threading.Thread(target=lambda:
                # bot.complete_obsidian_chat(blank_node['id'], canvas_file, nodes, edges,wdir)).start()
                threading.Thread(target=lambda: bot.complete_obsidian_chat(*args)).start()
        else:
            pass
        pass

        pass


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


__all__ = ['SetupAppStep', 'SetUpDatabaseStep', 'BeforeRunStep', 'LooperStep', 'AfterRunStep']


class SetupAppStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        config = configparser.ConfigParser()
        config_file = 'config.ini'
        try:
            config.read(config_file, encoding='utf-8')
        except configparser.ParsingError as e:
            error_str = ('Could not parse config.ini:' + str(e))
            monitor.error(error_str)
            raise e
        data.set('config', config)

        success, note_root, folders_list = initialize_with_config(config)
        if not success:
            monitor.error("Initialize with config failed. program will quit.")
            raise Exception("Initialize with config failed. program will quit.")

        util = ChatUtil()
        data.set('util', util)
        data.set('note_root', note_root)
        data.set('folders_list', folders_list)
        pass
        pass


class SetUpDatabaseStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        pass


class BeforeRunStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:

        process_file_flow = (
            WorkflowBuilder()
            .add_step(_chat_prepare_bot_step("Chat Prepare Bot", is_critical=True))
            .add_step(_chat_process_node_chain_step("Chat Process Node Chain", is_critical=True))
            .add_step(_process_messages_step("Process Messages", is_critical=True))
            .add_step(_chat_finalize_bot_step("Chat Finalize Bot", is_critical=True))
            .add_step(_chat_complete_step("Chat Complete", is_critical=True))
            .add_step(_chat_after_step("Chat After"))
            .build()
        )
        monitor.log('Setting up process file flow. Here is the flow preview')
        monitor.log("Processing canvas file.. ->\n" + str(process_file_flow))
        monitor.log('Setting up runner for process canvas file.')

        def file_processor(canvas_file, util, note_root):
            _, extension = os.path.splitext(canvas_file)
            if extension == '.canvas':
                try:
                    util.complete_obsidian_chat(canvas_file, note_root)
                    payload = {
                        'file': canvas_file,
                        'util': util,
                        'note_root': note_root
                    }
                    process_file_flow.run(payload, f"processing chat with :{canvas_file}")
                except Exception as e:
                    print('processing file error')
                    raise e
            pass

        data.set('runner', file_processor)
        pass


class LooperStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:

        note_root = data.get('note_root')
        folders_list = data.get('folders_list')
        util = data.get('util')
        file_processor = data.get('runner')

        # setup observers
        print('\033[92m' + 'Setting up observers...\n' + '\033[0m')
        observers = setup_observers(note_root, folders_list)
        # print a green color message to indicate the program is running.
        print('\033[92m' + 'ChatObsidian is running...\nConsole Gonna stop, ctrl + c to exit\n' + '\033[0m')
        try:
            while True:
                while current.queue.has_next():
                    file_processor(current.queue.dequeue(), util=util, note_root=note_root)
                time.sleep(2)
        except KeyboardInterrupt:
            for observer in observers:
                observer.stop()
            print('user stopped observers')
        for observer in observers:
            observer.join()
        print('program quit.')
        pass


class AfterRunStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        pass
