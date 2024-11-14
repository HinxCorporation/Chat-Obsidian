import shutil
import time
from abc import ABC, abstractmethod
from typing import List, Optional

from .flow_data import FlowData
from .monitor import Monitor


def separate_console_line(note_str=None, special_char='+', max_width=600, minimum_side_width=10) -> str:
    """
    Output a console line with a special character in the middle.
    :param note_str: The string to be displayed in the middle of the line.
    :param special_char: The special character to be used in the middle of the line.
    :param max_width: The maximum width of the console.
    :param minimum_side_width: The minimum width of the left and right sides of the console.
    :return: The console line with the special character in the middle.
    """
    # get console with for current console
    width = int(shutil.get_terminal_size().columns * 0.75)
    # max 600
    width = min(width, max_width)
    if note_str:
        side_len = minimum_side_width * 2 + 2
        if side_len >= width:
            return note_str
        max_note_len = width - side_len
        if len(note_str) > max_note_len:
            note_str = note_str[:max_note_len - 3] + '...'
        side_len = (width - 2 - len(note_str)) // 2
        return special_char * side_len + ' ' + note_str + ' ' + special_char * (width - side_len - len(note_str))
    # add note to console
    return '+' * width


class Step(ABC):
    def __init__(self, name: str, is_critical: bool = False):
        self.name = name
        self.is_critical = is_critical
        self.parent: Optional['Step'] = None

    @abstractmethod
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        pass

    def get_full_name(self) -> str:
        return f"{self.parent.get_full_name()}.{self.name}" if self.parent else self.name

    def __str__(self):
        return f"{self.name} (Step)"


class StepLoopBreak:
    """
    A breakable loop object.
    """

    def __init__(self):
        self.is_alive = True

    def __bool__(self):
        return self.is_alive

    def break_loop(self):
        self.is_alive = False

    def stop(self):
        self.break_loop()


class Condition:
    def __init__(self, condition_str: str, condition_func=None):
        """
        override is_satisfied is required or custom a condition method.
        :param condition_str: The condition string.
        :param condition_func: The custom condition method.
        """
        self.condition_str = condition_str
        self.custom_condition_method = condition_func

    def is_satisfied(self, data: FlowData) -> bool:
        if self.custom_condition_method:
            try:
                result: bool = self.custom_condition_method(data)
                return result
            except Exception as e:
                print(f"Error while executing custom condition method {self.custom_condition_method.__name__}")
                print(e)
                return False
        print(f"Condition {self.condition_str} is not implemented yet")
        return False

    def __str__(self):
        if self.custom_condition_method:
            return f"(func: {self.custom_condition_method.__name__})"
        return f"({self.condition_str})"


class IfStep(Step):
    def __init__(self, name: str):
        super().__init__(name)
        self.chain = []
        self.else_step: Optional[Step] = None
        pass

    def add_if(self, condition: Condition, next_step: Step) -> 'IfStep':
        self.chain.append((condition, next_step))
        return self

    def add_else_if(self, condition: Condition, next_step: Step) -> 'IfStep':
        self.add_if(condition, next_step)
        return self

    def add_else(self, next_step: Step) -> 'IfStep':
        self.else_step = next_step
        return self

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        if self.is_blank():
            print(f"No condition found in if step {self.name}")
            return
        if self.chain:
            for condition, next_step in self.chain:
                if condition.is_satisfied(data):
                    next_step.execute(data, monitor)
                    return
        if self.else_step:
            self.else_step.execute(data, monitor)
        pass

    def is_blank(self):
        """
        It means no condition and no else step.
        """
        if self.else_step:
            return False
        if not self.chain:
            return True
        if len(self.chain) == 0:
            return True
        return False

    def __str__(self):
        return f"{self.name} (IfStep)"


class SwitchStep(Step):
    def __init__(self, name: str, user_key: str, is_critical: bool = False, custom_case_func=None):
        super().__init__(name, is_critical)
        self.user_key = user_key
        self.default_step: Optional[Step] = None
        self.custom_case_method = custom_case_func
        self.cases = {}

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        monitor.log(separate_console_line(f"Begin execute switch {self.name}", special_char='*'))
        if not self.user_key or not data.has(self.user_key):
            monitor.warning(f"User key {self.user_key} not found in data, use default step")
            self._invoke_default_step(data, monitor)
        else:
            value = self._get_case_rt(data, monitor)
            if value and value in self.cases:
                step = self.cases[value]
                try:
                    step.execute(data, monitor)
                except Exception as e:
                    monitor.on_except(e)
                    if step.is_critical:
                        raise e
            else:
                self._invoke_default_step(data, monitor)
        monitor.log(separate_console_line(f"End execute switch {self.name}", special_char='*'))

    def _get_case_rt(self, data, monitor):
        if self.custom_case_method:
            try:
                args = {
                    "data": data,
                    "monitor": monitor,
                    'key': self.user_key,
                    'user_key': self.user_key
                }
                # filter args by function signature
                sig = self.custom_case_method.__signature__
                args = {k: v for k, v in args.items() if k in sig.parameters}
                result = self.custom_case_method(**args)
                # result = self.custom_case_method(data)
                return result
            except Exception as e:
                monitor.error(f"Error while executing custom case method {self.custom_case_method.__name__}")
                monitor.exception(e)
                # except but fallback to get value from data
        if data.has(self.user_key):
            return data.get(self.user_key)
        return None

    def _invoke_default_step(self, data, monitor):
        if self.default_step:
            try:
                self.default_step.execute(data, monitor)
            except Exception as e:
                monitor.on_except(e)
                if self.default_step.is_critical:
                    raise e
        else:
            monitor.error(f"No default step found for switch {self.name}")

    def add_case_multi(self, actions, step: Step) -> 'SwitchStep':
        for value in actions:
            self.add_case(value, step)
        return self

    def add_case(self, value, step: Step) -> 'SwitchStep':
        self.cases[value] = step
        step.parent = self
        return self

    def add_default(self, step: Step) -> 'SwitchStep':
        self.default_step = step
        step.parent = self
        return self

    def __str__(self):
        if self.custom_case_method:
            return f"{self.name} (SwitchStep) -> (custom case method {self.custom_case_method.__name__})"
        return f"{self.name} (SwitchStep) -> key={self.user_key}"


class ExecutableSteps(Step, ABC):
    def __init__(self, name: str, is_critical: bool = False):
        super().__init__(name, is_critical)
        self.steps: List[Step] = []

    def add_step(self, step: Step) -> 'ExecutableSteps':
        step.parent = self
        self.steps.append(step)
        return self

    def _execute_sub_steps(self, data: FlowData, monitor: Monitor) -> bool:
        """
        Execute all sub steps of this step.
        :param data: The data object to be used by the steps.
        :param monitor: The monitor object to be used by the steps.
        :return: True if all sub steps executed successfully, False otherwise.
        """
        total = len(self.steps)
        monitor.log(separate_console_line(f"Begin execute sub steps : total {total}"))
        counter = 0
        for sub_step in self.steps:
            counter += 1
            monitor.log(f'--> On step {counter}/{total} : {sub_step.get_full_name()}')
            if not monitor.can_continue():
                return False
            try:
                sub_step.execute(data, monitor)
            except Exception as e:
                monitor.on_except(e)
                monitor.error(f"Error executing sub step {sub_step.get_full_name()}")
                if sub_step.is_critical:
                    return False

        # for counter, sub_step in enumerate(self.steps, 1):
        #     monitor.log(f'--> On step {counter}/{total} : {sub_step.get_full_name()}')
        #     if not monitor.can_continue():
        #         return False
        #     try:
        #         sub_step.execute(data, monitor)
        #     except Exception as e:
        #         monitor.on_except(e)
        #         monitor.error(f"Error executing sub step {sub_step.get_full_name()}")
        #         if sub_step.is_critical:
        #             return False
        return True

    pass


class StepLoop(ExecutableSteps):
    """
    A step that executes a list of sub steps in a loop.
    """

    def __init__(self, name: str, is_critical: bool = False, looper: StepLoopBreak = None):
        """
        Custom a breakable loop.
        :param name: The name of the loop.
        :param is_critical: Whether the loop is critical or not.
        :param looper: The breakable loop object.
        """
        super().__init__(name, is_critical)
        self.looper = looper or StepLoopBreak()
        self.steps: List[Step] = []
        self.loop_times = 0

    def execute(self, data: FlowData, monitor: Monitor):
        monitor.log(separate_console_line(f"Begin execute loop {self.name}", special_char='='))
        while self.is_alive():
            self.loop_times += 1
            monitor.log(f"Executing {self.name} (No. {self.loop_times})")
            data.set(f"{self.name}_iteration", self.loop_times)

            try:
                if not self._execute_sub_steps(data, monitor):
                    break
            except Exception as e:
                monitor.on_except(e)
                monitor.error(f"Errors while looping {self.name} , will sleep for 10 seconds and continue")
                time.sleep(10)
            pass
        monitor.log(separate_console_line(f"Loop {self.name} finished", special_char='='))

    def break_loop(self):
        self.looper.break_loop()

    def stop(self):
        self.looper.stop()

    def is_alive(self):
        return self.looper.is_alive

    def __str__(self):
        return f"Flow [LOOP]: {self.name}"


class StepGroup(ExecutableSteps):
    def __init__(self, name: str, is_critical: bool = False, max_iterations: int = 1):
        """
        A step that executes a list of sub steps in a group.
        :param name: The name of the group.
        :param is_critical: Whether the group is critical or not.
        :param max_iterations: The maximum number of iterations.
        """
        super().__init__(name, is_critical)
        self.steps: List[Step] = []
        self.max_iterations = max_iterations

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        monitor.log(separate_console_line(f"Begin execute group {self.name}", special_char='-'))
        for iteration in range(self.max_iterations):
            monitor.log(f"Executing {self.name} (loop {iteration + 1}/{self.max_iterations})")
            data.set(f"{self.name}_iteration", iteration)
            if not self._execute_sub_steps(data, monitor):
                break
            if data.get(f"{self.name}_break"):
                break
        monitor.log(separate_console_line(f"Iteration {self.name} finished", special_char='-'))

    def __str__(self):
        return f"{self.name} (Group, max_iterations={self.max_iterations})"
