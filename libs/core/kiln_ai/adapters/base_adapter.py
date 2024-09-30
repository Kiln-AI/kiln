import json
from abc import ABCMeta, abstractmethod
from typing import Dict

from kiln_ai.datamodel import Task
from kiln_ai.datamodel.json_schema import validate_schema


class BaseAdapter(metaclass=ABCMeta):
    def __init__(self, kiln_task: Task):
        self.kiln_task = kiln_task

        self.output_schema = self.kiln_task.output_json_schema

        self.input_schema = self.kiln_task.input_json_schema

    async def invoke(self, input: Dict | str) -> Dict | str:
        # validate input
        if self.input_schema is not None:
            if not isinstance(input, dict):
                raise ValueError(f"structured input is not a dict: {input}")
            validate_schema(input, self.input_schema)

        # Run
        result = await self._run(input)

        # validate output
        if self.output_schema is not None:
            if not isinstance(result, dict):
                raise RuntimeError(f"structured response is not a dict: {result}")
            validate_schema(result, self.output_schema)
        else:
            if not isinstance(result, str):
                raise RuntimeError(
                    f"response is not a string for non-structured task: {result}"
                )
        return result

    def has_strctured_output(self) -> bool:
        return self.output_schema is not None

    @abstractmethod
    async def _run(self, input: Dict | str) -> Dict | str:
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

    # Can be overridden to add more information to the user message
    def build_user_message(self, input: Dict | str) -> str:
        if isinstance(input, Dict):
            return f"The input is:\n{json.dumps(input, indent=2)}"

        return f"The input is:\n{input}"
