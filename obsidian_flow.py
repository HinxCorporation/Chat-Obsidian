import os
from Workflow import WorkflowBuilder
from Workflow.main import run_demo_workflow
from obsidian_custom_flows import SetupAppStep, SetUpDatabaseStep, BeforeRunStep, LooperStep, AfterRunStep


def run():
    (WorkflowBuilder()
     .add_step(SetupAppStep("Setup App", is_critical=True))
     .add_step(SetUpDatabaseStep("Set Up Database", is_critical=True))
     .add_step(BeforeRunStep("Before Run", is_critical=True))
     .add_step(LooperStep("Loop", is_critical=True))
     .add_step(AfterRunStep("After Run"))
     .build()
     ).run(flow_name="Chat Bot Workflow")


if __name__ == "__main__":
    # if os env debug run demo workflow
    if os.getenv("DEBUG", False):
        run_demo_workflow()
    else:
        run()
        print("Workflow completed")
