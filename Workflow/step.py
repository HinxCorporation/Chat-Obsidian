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
        self.parent: Optional['StepGroup'] = None

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
        for iteration in range(self.max_iterations):
            monitor.log(f"Executing {self.name} (loop {iteration + 1}/{self.max_iterations})")
            data.set(f"{self.name}_iteration", iteration)
            if not self._execute_sub_steps(data, monitor):
                break
            if data.get(f"{self.name}_break"):
                break

        monitor.log(separate_console_line(f"Iteration {self.name} finished"))

    def __str__(self):
        return f"{self.name} (Group, max_iterations={self.max_iterations})"
