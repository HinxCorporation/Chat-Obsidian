import threading

from Workflow import WorkflowBuilder, Step, FlowData, Monitor


class FlowV1:

    @staticmethod
    def create():
        return (
            WorkflowBuilder()
            .add_step(ensure_flow_data("1. Ensure Flow Data", is_critical=True))
            .add_step(set_up_running_args("2. Set Up Running Args", is_critical=True))
            .add_step(set_up_chat_info("3. Set Up Chat Info", is_critical=True))
            .add_step(processing_chat("4. Processing Chat", is_critical=True))
            .add_step(finished_chat("5. Finished Chat", is_critical=True))
            .build()
        )


class ensure_flow_data(Step):

    def execute(self, data: FlowData, monitor: Monitor):
        require_list = ['node', 'file', 'ins_custom', 'edges', 'nodes', 'note_root']
        # run_args create from flow. Note: run_args is not required
        optional_list = ['skip_1']
        for item in require_list:
            if not data.has(item):
                # flow could not be continued
                raise ValueError(f"FlowData missing required item: {item}")
        for item in optional_list:
            if not data.has(item):
                pass
        pass


class set_up_running_args(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        node = data.get('node')
        canvas_file = data.get('file')
        ins_custom = data.get('ins_custom')

        if data.has('skip_1'):
            skip_1 = data.get('skip_1')
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
        data.set('run_args', run_args)


class set_up_chat_info(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        node = data.get("node")
        run_args = data.get("run_args")

        _title = node.get('title')
        if not _title:
            _title = node.get('name')
        if _title:
            run_args['title'] = _title
        _prompt = node.get('prompt')
        if _prompt:
            run_args['prompt'] = _prompt
        pass


class processing_chat(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        ins_custom = data.get("ins_custom")
        run_args = data.get("run_args")
        monitor.log(f"Obsidian will complete at background.")
        threading.Thread(target=lambda: ins_custom.processing(**run_args)).start()
        pass


class finished_chat(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        pass

# ###################################OBSOLETE#################################################
#
# if skip_1:
#     ins_custom.exclude_first_node = True
# # requires node_id, canvas_files,root_dir,edges,nodes,**args
# edges = data.get('edges')
# nodes = data.get('nodes')
#
# run_args = {
#     'node_id': node['id'],
#     'canvas_file': canvas_file,
#     'root_dir': data.get('note_root'),
#     'edges': edges,
#     'nodes': nodes,
# }
# _title = node.get('title')
# if not _title:
#     _title = node.get('name')
# if _title:
#     run_args['title'] = _title
# _prompt = node.get('prompt')
# if _prompt:
#     run_args['prompt'] = _prompt
#
# self.monitor.log(f"Obsidian will complete at background.")
# threading.Thread(target=lambda: ins_custom.processing(**run_args)).start()
