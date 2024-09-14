from .flow_data import FlowData
from .monitor import Monitor
from .step import Step, StepGroup
from .workflow import WorkflowBuilder


class SimpleStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        if '.' in self.name:
            monitor.log(f"\tSubstep: {self.name}")
        else:
            monitor.log(f"Executing step: {self.name}")


def run_demo_workflow():
    """
    an example usage of the WorkflowBuilder and Step classes
    """
    workflow = (
        WorkflowBuilder()
        .add_step(SimpleStep("Step 1", is_critical=True))
        .add_step(
            StepGroup("Group 1", max_iterations=1, is_critical=True)
            .add_step(SimpleStep("Substep 1.1", is_critical=True))
            .add_step(SimpleStep("Substep 1.2", is_critical=True))
            .add_step(SimpleStep("Substep 1.3", is_critical=True))
        )
        .add_step(SimpleStep("Step 2", is_critical=True))
        .add_step(SimpleStep("Step 3", is_critical=True))
        .build()
    )

    workflow.preview()
    result = workflow.run()
    print('--------------execution result------------------')
    print("result:", result)


if __name__ == "__main__":
    run_demo_workflow()
