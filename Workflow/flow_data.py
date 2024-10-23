from typing import Any, Dict


class FlowData:
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        self._data.update(data)

    def has(self, key: str) -> bool:
        return key in self._data

    def clone(self):
        new_data = FlowData()
        new_data._data = self._data.copy()
        return new_data

    def copy(self):
        return self.clone()
