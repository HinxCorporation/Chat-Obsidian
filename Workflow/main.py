import time

from .flow_data import FlowData
from .monitor import Monitor
from .step import Step, StepGroup, StepLoopBreak, StepLoop, Condition, IfStep, SwitchStep
from .workflow import WorkflowBuilder


class SimpleStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        if '.' in self.name:
            monitor.log(f"\tSubstep: {self.name}")
        else:
            monitor.log(f"Executing step: {self.name}")


class Wait1sStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        import time
        time.sleep(1)


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


class sw_condition(Condition):
    def __init__(self, name: str):
        super().__init__(name)
        self.default_value = False

    def is_satisfied(self, data: FlowData) -> bool:
        self.default_value = not self.default_value
        return self.default_value


class Light_On_Step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        monitor.warning("Light on")


class Light_Off_Step(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        monitor.error("Light off")


def run_demo_workflow():
    """
    an example usage of the WorkflowBuilder and Step classes
    """
    loop_breaker = StepLoopBreak()
    btn = sw_condition('Touch me for reverse')
    user_key = 'auth'
    workflow = (
        WorkflowBuilder()
        .add_step(SimpleStep("Step 1", is_critical=True))
        # An example of adding a substep group via custom iter count
        .add_step(
            StepGroup("ITER_INT:", max_iterations=3, is_critical=True)
            .add_step(SimpleStep("Substep 1.1", is_critical=True))
            .add_step(SimpleStep("Substep 1.2", is_critical=True))
            # An example of adding a substep group via custom iter condition
            .add_step(IfStep("If lights on?")
                      .add_if(btn, Light_On_Step(" . . . . "))
                      .add_else(Light_Off_Step(" * * * * "))
                      )
            # rev. on off on
        )
        # An example of adding a substep group via custom iter condition
        .add_step(StepLoop("LOOP", False, loop_breaker)
                  .add_step(SimpleStep("Loop QAQ -- Normal Step", is_critical=False))
                  .add_step(Wait1sStep("Wait 1s", is_critical=True))
                  .add_step(CountDownStep("In step countdown break loop", 2, loop_breaker))
                  )
        # An example of adding a switch step
        .add_step(SwitchStep("Switch demo", user_key)
                  .add_case('hinx', SimpleStep("Switch demo hinx", is_critical=True))
                  .add_case('admin', SimpleStep("Switch demo admin", is_critical=True))
                  .add_default(SimpleStep("Switch demo default", is_critical=True))
                  )
        # rev. default, because Tom not on the list
        .add_step(SimpleStep("Step 3", is_critical=True))
        .build()
    )

    workflow.preview()
    result = workflow.run({
        'auth': 'tom'
    })
    time.sleep(0.5)
    print('--------------execution result------------------')
    print("result:", result)


if __name__ == "__main__":
    run_demo_workflow()
