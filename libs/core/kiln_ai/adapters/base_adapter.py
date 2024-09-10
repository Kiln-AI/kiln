from abc import ABCMeta, abstractmethod
from typing import Dict

from kiln_ai.datamodel.json_schema import validate_schema
from kiln_ai.datamodel.models import Task


class BaseAdapter(metaclass=ABCMeta):
    def __init__(self, kiln_task: Task):
        self.kiln_task = kiln_task
        self._is_structured_output = self.kiln_task.output_json_schema is not None

    async def invoke(self, input: str) -> Dict | str:
        result = await self._run(input)
        if self._is_structured_output:
            if not isinstance(result, dict):
                raise RuntimeError(f"structured response is not a dict: {result}")
            if self.kiln_task.output_json_schema is None:
                raise ValueError(
                    f"output_json_schema is not set for task {self.kiln_task.name}"
                )
            validate_schema(result, self.kiln_task.output_json_schema)
        else:
            if not isinstance(result, str):
                raise RuntimeError(
                    f"response is not a string for non-structured task: {result}"
                )
        return result

    @abstractmethod
    async def _run(self, input: str) -> Dict | str:
        pass

    # override for adapter specific instructions (e.g. tool calling, json format, etc)
    def adapter_specific_instructions(self) -> str | None:
        return None


class BasePromptBuilder(metaclass=ABCMeta):
    def __init__(self, task: Task, adapter: BaseAdapter | None = None):
        self.task = task
        self.adapter = adapter

    @abstractmethod
    def build_prompt(self) -> str:
        pass

    @abstractmethod
    def build_user_message(self, input: str) -> str:
        pass
