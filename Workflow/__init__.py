__version__ = "0.1.0"  # 添加这行

from .example_steps import DataLoadStep as ExampleLoadData, \
    ProcessingStep as ExampleProcessing, ValidationStep as ExampleValidation
from .flow_data import FlowData
from .monitor import Monitor
from .step import Step, StepLoop, StepLoopBreak, StepGroup, Condition, IfStep,SwitchStep, separate_console_line
from .workflow import Workflow, WorkflowBuilder

__all__ = [
    'Workflow',
    'WorkflowBuilder',
    'FlowData',
    'Monitor',
    'Step',
    'StepGroup',
    'StepLoop',
    'SwitchStep',
    'StepLoopBreak',
    'Condition',
    'IfStep',
    'separate_console_line',
    'ExampleLoadData',
    'ExampleProcessing',
    'ExampleValidation'
]
