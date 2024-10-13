import json
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Dict

from kiln_ai.datamodel import (
    DataSourceType,
    Task,
    TaskInput,
    TaskOutput,
)
from kiln_ai.datamodel.json_schema import validate_schema
from kiln_ai.utils.config import Config


@dataclass
class AdapterInfo:
    adapter_name: str
    model_name: str
    model_provider: str
    prompt_builder_name: str


class BaseAdapter(metaclass=ABCMeta):
    def __init__(self, kiln_task: Task):
        self.kiln_task = kiln_task
        self.output_schema = self.kiln_task.output_json_schema
        self.input_schema = self.kiln_task.input_json_schema

    async def invoke(
        self,
        input: Dict | str,
        input_source: DataSourceType = DataSourceType.human,
    ) -> Dict | str:
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

        # Save the run and output
        if Config.shared().autosave_runs:
            self.save_run(input, input_source, result)

        return result

    def has_structured_output(self) -> bool:
        return self.output_schema is not None

    @abstractmethod
    def adapter_info(self) -> AdapterInfo:
        pass

    @abstractmethod
    async def _run(self, input: Dict | str) -> Dict | str:
        pass

    # override for adapter specific instructions (e.g. tool calling, json format, etc)
    def adapter_specific_instructions(self) -> str | None:
        return None

    # create a run and task output
    def save_run(
        self, input: Dict | str, input_source: DataSourceType, output: Dict | str
    ) -> TaskInput:
        # Convert input and output to JSON strings if they are dictionaries
        input_str = json.dumps(input) if isinstance(input, dict) else input
        output_str = json.dumps(output) if isinstance(output, dict) else output

        # Check for existing task inputs with matching parent.id, input, and source
        existing_task_input = next(
            (
                task_input
                for task_input in self.kiln_task.runs()
                if (parent_task := task_input.parent_task()) is not None
                and parent_task.id == self.kiln_task.id
                and task_input.input == input_str
                and task_input.source == input_source
            ),
            None,
        )

        if existing_task_input:
            task_input = existing_task_input
        else:
            task_input = TaskInput(
                parent=self.kiln_task,
                input=input_str,
                source=input_source,
            )
            task_input.save_to_file()

        # Check for existing TaskOutput with matching parent.id, input, and source
        existing_output = next(
            (
                output
                for output in task_input.outputs()
                if (parent_task_input := output.parent_task_input()) is not None
                and parent_task_input.id == task_input.id
                and output.output == output_str
            ),
            None,
        )

        if existing_output:
            return task_input

        # Create a new TaskOutput for the existing or new TaskInput
        task_output = TaskOutput(
            parent=task_input,
            output=output_str,
            # Synthetic since an adapter, not a human, is creating this
            source=DataSourceType.synthetic,
            source_properties=self._properties_for_task_output(),
        )
        task_output.save_to_file()
        return task_input

    def _properties_for_task_output(self) -> Dict:
        props = {}

        # creator user id
        creator = Config.shared().user_id
        if creator and creator != "":
            props["creator"] = creator

        # adapter info
        adapter_info = self.adapter_info()
        props["adapter_name"] = adapter_info.adapter_name
        props["model_name"] = adapter_info.model_name
        props["model_provider"] = adapter_info.model_provider
        props["prompt_builder_name"] = adapter_info.prompt_builder_name

        return props


class BasePromptBuilder(metaclass=ABCMeta):
    def __init__(self, task: Task, adapter: BaseAdapter | None = None):
        self.task = task
        self.adapter = adapter

    @abstractmethod
    def build_prompt(self) -> str:
        pass

    # override to change the name of the prompt builder (if changing class names)
    def prompt_builder_name(self) -> str:
        return self.__class__.__name__

    # Can be overridden to add more information to the user message
    def build_user_message(self, input: Dict | str) -> str:
        if isinstance(input, Dict):
            return f"The input is:\n{json.dumps(input, indent=2)}"

        return f"The input is:\n{input}"
