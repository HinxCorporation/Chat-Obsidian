import configparser
import os
import time

from ChatObsidian.ObsidianShared import current
from ChatObsidian.WatcherUtil import initialize_with_config, setup_observers
from Workflow import FlowData
from Workflow import Monitor
from Workflow import Step
from Workflow import WorkflowBuilder
from .obsidian_node_to_chain import create_flow as create_chain_to_message_flow
from .obsidian_processing import (_chat_after_step, _chat_complete_step,
                                  _chat_finalize_bot_step, _chat_prepare_bot_step,
                                  _chat_process_node_chain_step, _process_messages_step)
from ..chat_obsidian import ChatUtil


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

        chain_to_message_flow = create_chain_to_message_flow()

        monitor.log('Setting up process file flow. Here is the flow preview')
        monitor.log("Processing canvas file.. ->\n" + str(process_file_flow))
        monitor.log('Setting up runner for process canvas file.')

        def file_processor(canvas_file, util, note_root):
            if not os.path.exists(canvas_file):
                print(f"canvas file {canvas_file} does not exist.")
                return
            _, extension = os.path.splitext(canvas_file)
            if extension == '.canvas':
                try:
                    # util.complete_obsidian_chat(canvas_file, note_root)
                    payload = {
                        'file': canvas_file,
                        'util': util,
                        'note_root': note_root,
                        '_use_built_in_chains': False,
                        'chain_flow': chain_to_message_flow
                    }
                    _, canvas_short_name = os.path.split(canvas_file)
                    process_file_flow.run(payload, f"processing chat with :{canvas_short_name}")
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
        file_processor = data.get('runner', None)
        if not file_processor:
            raise Exception("No file processor found. program will quit.")

        # setup observers
        monitor.log('Setting up observers.')
        observers = setup_observers(note_root, folders_list)
        # print a green color message to indicate the program is running.
        monitor.log('ChatObsidian is running. Console Gonna stop, ctrl + c to exit.')
        try:
            while True:
                while current.queue.has_next():
                    target_file = current.queue.dequeue()
                    if '.ai.assets' in target_file:
                        continue
                    file_processor(target_file, util=util, note_root=note_root)
                    time.sleep(0.1)  # sleep for 0.1 seconds to avoid too frequent file processing.
        except KeyboardInterrupt:
            for observer in observers:
                observer.stop()
            monitor.warning('KeyboardInterrupt received. Program will quit.')
        for observer in observers:
            observer.join()
        monitor.log('Program quit.')
        pass


class AfterRunStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        pass
