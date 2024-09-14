from abc import ABC, abstractmethod
from typing import List, Optional

from .flow_data import FlowData
from .monitor import Monitor


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


class StepGroup(Step):
    def __init__(self, name: str, is_critical: bool = False, max_iterations: int = 1):
        super().__init__(name, is_critical)
        self.steps: List[Step] = []
        self.max_iterations = max_iterations

    def add_step(self, step: Step) -> 'StepGroup':
        step.parent = self
        self.steps.append(step)
        return self

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        for iteration in range(self.max_iterations):
            monitor.log(f"Executing {self.name} (loop {iteration+1}/{self.max_iterations})")
            data.set(f"{self.name}_iteration", iteration)
            
            if not self._execute_substeps(data, monitor):
                break

            if data.get(f"{self.name}_break"):
                break

    def _execute_substeps(self, data: FlowData, monitor: Monitor) -> bool:
        total = len(self.steps)
        monitor.log(f"Begin execute sub steps : total {total}")
        
        for counter, sub_step in enumerate(self.steps, 1):
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
        
        return True

    def __str__(self):
        return f"{self.name} (Group, max_iterations={self.max_iterations})"
