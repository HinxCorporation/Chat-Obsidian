from .flow_data import FlowData
from .monitor import Monitor
from .step import Step, StepGroup, StepLoopBreak, StepLoop
from .workflow import WorkflowBuilder
import time


class SimpleStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        if '.' in self.name:
            monitor.log(f"\tSubstep: {self.name}")
        else:
            monitor.log(f"Executing step: {self.name}")


class Wait2sStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        import time
        time.sleep(2)


class CountDownStep(Step):
    def __init__(self, name: str, count: int, looper: StepLoopBreak):
        super().__init__(name)
        self.count = count

        self.looper = looper

    def execute(self, data: FlowData, monitor: Monitor) -> None:
        self.count -= 1
        if self.count > 0:
            monitor.log(f"Countdown: {self.count}")
        else:
            monitor.log("Countdown complete")
            self.looper.break_loop()
        pass


def run_demo_workflow():
    """
    an example usage of the WorkflowBuilder and Step classes
    """
    loop_breaker = StepLoopBreak()
    workflow = (
        WorkflowBuilder()
        .add_step(SimpleStep("Step 1", is_critical=True))
        .add_step(
            StepGroup("ITER_INT:", max_iterations=2, is_critical=True)
            .add_step(SimpleStep("Substep 1.1", is_critical=True))
            .add_step(SimpleStep("Substep 1.2", is_critical=True))
        )
        .add_step(StepLoop("LUP:", False, loop_breaker)
                  .add_step(SimpleStep("Loop QAQ", is_critical=True))
                  .add_step(Wait2sStep("Wait 2s", is_critical=True))
                  .add_step(CountDownStep("In step countdown break loop", 2, loop_breaker))
                  )
        .add_step(SimpleStep("Step 2", is_critical=True))
        .add_step(SimpleStep("Step 3", is_critical=True))
        .build()
    )

    workflow.preview()
    result = workflow.run()
    time.sleep(1)
    print('--------------execution result------------------')
    print("result:", result)


if __name__ == "__main__":
    run_demo_workflow()
