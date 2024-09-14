from .flow_data import FlowData
from .monitor import Monitor
from .step import Step


class DataLoadStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        # 模拟数据加载
        data.set("loaded_data", [1, 2, 3, 4, 5])
        monitor.log("Data loaded successfully")


class ProcessingStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        loaded_data = data.get("loaded_data")
        processed_data = [x * 2 for x in loaded_data]
        data.set("processed_data", processed_data)
        monitor.log("Data processed successfully")


class ValidationStep(Step):
    def execute(self, data: FlowData, monitor: Monitor) -> None:
        processed_data = data.get("processed_data")
        if sum(processed_data) > 50:
            raise ValueError("Processed data sum is too high")
        monitor.log("Data validated successfully")
