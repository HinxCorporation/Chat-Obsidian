from typing import List, Optional, Dict

from .flow_data import FlowData
from .monitor import Monitor
from .step import Step, StepGroup


class WorkflowBuilder:
    def __init__(self):
        self.steps: List[Step] = []

    def add_step(self, step: Step) -> 'WorkflowBuilder':
        self.steps.append(step)
        return self

    def remove_step(self, step_name: str) -> 'WorkflowBuilder':
        self.steps = [step for step in self.steps if step.name != step_name]
        return self

    def build(self) -> 'Workflow':
        return Workflow(self.steps)


class Workflow:
    def __init__(self, steps: List[Step]):
        self.steps = steps

    def run(self, initial_data: Optional[Dict] = None, flow_name: str = "non-named-flow",
            custom_monitor: Monitor = None,
            enable_monitor_log=False) -> FlowData:
        """
        Runs the workflow with the given initial data.
        :param initial_data: Initial data to be passed to the first step.
        :param flow_name: Name of the flow.
        :param custom_monitor: Custom monitor to use instead of the default one.
        :param enable_monitor_log: Whether to enable logging for the monitor.
        :return: The final data after running the workflow.
        """
        data = FlowData()
        if initial_data:
            data.update(initial_data)
        if custom_monitor:
            monitor = custom_monitor
        else:
            monitor = Monitor(flow_name, enable_monitor_file_log=enable_monitor_log)

        for step in self.steps:
            if not monitor.can_continue():
                break

            try:
                step.execute(data, monitor)
            except Exception as e:
                monitor.on_except(e)
                if step.is_critical:
                    raise e

        return data

    def preview(self):
        """
        Prints a preview of the workflow, showing the steps in order.
        """
        print("Workflow Preview:")
        print("=================")
        self._print_steps(self.steps)
        print("=================")

    def _print_steps(self, steps: List[Step], indent: str = ""):
        for step in steps:
            print(f"{indent}{step}")
            if isinstance(step, StepGroup):
                self._print_steps(step.steps, indent + "  ")

    def __str__(self):
        return '\n'.join(f"{i}. {step.get_full_name()}" for i, step in enumerate(self.steps, 1))

    def __repr__(self):
        return f"Workflow(steps={len(self.steps)})"
