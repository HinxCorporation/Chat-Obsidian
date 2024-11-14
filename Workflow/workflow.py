from typing import List, Optional, Dict

from .flow_data import FlowData
from .monitor import Monitor
from .step import Step, StepGroup, StepLoop, ExecutableSteps, SwitchStep, IfStep


tab_str = "  "


def get_step_expression(steps: List[Step], indent: str = ""):
    lines = []
    next_indent = indent + tab_str
    for step in steps:
        lines.append(f"{indent}{step}")
        # print(f"{indent}{step}", end=ends)
        if isinstance(step, StepGroup):
            sub_lines = get_step_expression(step.steps, next_indent)
            for line in sub_lines:
                lines.append(line)
            # self._print_steps(step.steps, indent + "  ")
        elif isinstance(step, StepLoop):
            sub_lines = get_step_expression(step.steps, indent + "  ")
            for line in sub_lines:
                lines.append(line)
        elif isinstance(step, ExecutableSteps):
            sub_lines = get_step_expression(step.steps, indent + "  ")
            for line in sub_lines:
                lines.append(line)
        elif isinstance(step, SwitchStep):
            cases = step.cases
            for case in cases:
                sub_step = cases[case]
                sub_lines = get_step_expression([sub_step])
                if len(sub_lines) == 1:
                    lines.append(f"{next_indent} > {case}: -> {sub_lines[0]}")
                else:
                    lines.append(f"{next_indent} > {case}:")
                    for line in sub_lines:
                        lines.append(f"{next_indent}  --> {line}:")
            if step.default_step:
                sub_lines = get_step_expression([step.default_step])
                if len(sub_lines) == 1:
                    lines.append(f"{next_indent} > default: -> {sub_lines[0]}")
                else:
                    lines.append(f"{next_indent} > default:")
                    for line in sub_lines:
                        lines.append(f"{next_indent}  --> {line}:")
        elif isinstance(step, IfStep):
            if step.is_blank():
                lines.append(f"{next_indent} > -")
            else:
                if step.chain is not None and len(step.chain) > 0:
                    position = 0
                    for condition, sub_step in step.chain:
                        sub_lines = get_step_expression([sub_step])
                        mark = "if" if position == 0 else "else if"
                        if len(sub_lines) == 1:
                            lines.append(f"{next_indent} {mark} {condition}: -> {sub_lines[0]}")
                        else:
                            lines.append(f"{next_indent} {mark} {condition}:")
                            for line in sub_lines:
                                lines.append(f"{next_indent}  --> {line}:")
                        position += 1
                if step.else_step:
                    sub_lines = get_step_expression([step.else_step])
                    if len(sub_lines) == 1:
                        lines.append(f"{next_indent} else: -> {sub_lines[0]}")
                    else:
                        lines.append(f"{next_indent} else:")
                        for line in sub_lines:
                            lines.append(f"{next_indent}  --> {line}:")
    return lines


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

    def run(self,
            initial_data: Optional[Dict] = None,
            flow_name: str = "non-named-flow",
            custom_monitor: Monitor = None,
            enable_monitor_log=False) -> FlowData:
        """
        Runs the workflow with the given initial data.
        :param initial_data: Initial data to be passed to the first step.
        :param flow_name: Name of the flow.
        :param custom_monitor: Custom monitor to use instead of the default one.
        :param enable_monitor_log: Whether to enable logging file for the monitor.
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
        print("==================================")
        lines = get_step_expression(self.steps)
        # self._print_steps(self.steps)
        print('\n'.join(lines))
        print("==================================")

    def _print_steps(self, steps: List[Step], indent: str = "", ends='\n'):
        for step in steps:
            print(f"{indent}{step}", end=ends)
            if isinstance(step, StepGroup):
                self._print_steps(step.steps, indent + "  ")
            elif isinstance(step, StepLoop):
                self._print_steps(step.steps, indent + "  ")
            elif isinstance(step, ExecutableSteps):
                self._print_steps(step.steps, indent + "  ")
            elif isinstance(step, SwitchStep):
                for case, sub_step in step.cases:
                    print(f"{indent} > {case}: -> ", end='')
                    self._print_steps(sub_step)
            elif isinstance(step, IfStep):
                pass

    def __str__(self):
        return '\n'.join(f"{i}. {step.get_full_name()}" for i, step in enumerate(self.steps, 1))

    def __repr__(self):
        return f"Workflow(steps={len(self.steps)})"
