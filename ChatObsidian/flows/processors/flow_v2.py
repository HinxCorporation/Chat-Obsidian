from Workflow import WorkflowBuilder, Step, FlowData, Monitor
from .flow_v1 import ensure_flow_data, set_up_chat_info, processing_chat, finished_chat


class FlowV2:
    @staticmethod
    def create():
        return (
            WorkflowBuilder()
            .add_step(ensure_flow_data("1. Ensure Flow Data", is_critical=True))
            .add_step(set_up_running_args("2. Set Up Running Args [ SPE COMPLEX ]", is_critical=True))
            .add_step(set_up_chat_info("3. Set Up Chat Info", is_critical=True))
            .add_step(processing_chat("4. Processing Chat", is_critical=True))
            .add_step(finished_chat("5. Finished Chat", is_critical=True))
            .build()
        )


class set_up_running_args(Step):
    def execute(self, data: FlowData, monitor: Monitor):
        node = data.get('node')
        canvas_file = data.get('file')
        ins_custom = data.get('ins_custom')
        ins_custom.exclude_first_node = False
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
        pass
