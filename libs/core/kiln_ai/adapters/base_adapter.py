import json
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Dict

from kiln_ai.datamodel import (
    DataSource,
    DataSourceType,
    Task,
    TaskOutput,
    TaskRun,
)
from kiln_ai.datamodel.json_schema import validate_schema
from kiln_ai.utils.config import Config

from .prompt_builders import BasePromptBuilder, SimplePromptBuilder


@dataclass
class AdapterInfo:
    adapter_name: str
    model_name: str
    model_provider: str
    prompt_builder_name: str


class BaseAdapter(metaclass=ABCMeta):
    def __init__(
        self, kiln_task: Task, prompt_builder: BasePromptBuilder | None = None
    ):
        self.prompt_builder = prompt_builder or SimplePromptBuilder(kiln_task)
        self.kiln_task = kiln_task
        self.output_schema = self.kiln_task.output_json_schema
        self.input_schema = self.kiln_task.input_json_schema

    async def invoke_returning_raw(
        self,
        input: Dict | str,
        input_source: DataSource | None = None,
    ) -> Dict | str:
        result = await self.invoke(input, input_source)
        if self.kiln_task.output_json_schema is None:
            return result.output.output
        else:
            return json.loads(result.output.output)

    async def invoke(
        self,
        input: Dict | str,
        input_source: DataSource | None = None,
    ) -> TaskRun:
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

        # Generate the run and output
        run = self.generate_run(input, input_source, result)

        # Save the run if configured to do so, and we have a path to save to
        if Config.shared().autosave_runs and self.kiln_task.path is not None:
            run.save_to_file()
        else:
            # Clear the ID to indicate it's not persisted
            run.id = None

        return run

    def has_structured_output(self) -> bool:
        return self.output_schema is not None

    @abstractmethod
    def adapter_info(self) -> AdapterInfo:
        pass

    @abstractmethod
    async def _run(self, input: Dict | str) -> Dict | str:
        pass

    def build_prompt(self) -> str:
        prompt = self.prompt_builder.build_prompt()
        adapter_instructions = self.adapter_specific_instructions()
        if adapter_instructions is not None:
            prompt += f"# Format Instructions\n\n{adapter_instructions}\n\n"
        return prompt

    # override for adapter specific instructions (e.g. tool calling, json format, etc)
    def adapter_specific_instructions(self) -> str | None:
        return None

    # create a run and task output
    def generate_run(
        self, input: Dict | str, input_source: DataSource | None, output: Dict | str
    ) -> TaskRun:
        # Convert input and output to JSON strings if they are dictionaries
        input_str = json.dumps(input) if isinstance(input, dict) else input
        output_str = json.dumps(output) if isinstance(output, dict) else output

        # If no input source is provided, use the human data source
        if input_source is None:
            input_source = DataSource(
                type=DataSourceType.human,
                properties={"created_by": Config.shared().user_id},
            )

        new_task_run = TaskRun(
            parent=self.kiln_task,
            input=input_str,
            input_source=input_source,
            output=TaskOutput(
                output=output_str,
                # Synthetic since an adapter, not a human, is creating this
                source=DataSource(
                    type=DataSourceType.synthetic,
                    properties=self._properties_for_task_output(),
                ),
            ),
        )

        exclude_fields = {
            "id": True,
            "created_at": True,
            "updated_at": True,
            "path": True,
            "output": {"id": True, "created_at": True, "updated_at": True},
        }
        new_run_dump = new_task_run.model_dump(exclude=exclude_fields)

        # Check if the same run already exists
        existing_task_run = next(
            (
                task_run
                for task_run in self.kiln_task.runs()
                if task_run.model_dump(exclude=exclude_fields) == new_run_dump
            ),
            None,
        )
        if existing_task_run:
            return existing_task_run

        return new_task_run

    def _properties_for_task_output(self) -> Dict[str, str | int | float]:
        props = {}

        # adapter info
        adapter_info = self.adapter_info()
        props["adapter_name"] = adapter_info.adapter_name
        props["model_name"] = adapter_info.model_name
        props["model_provider"] = adapter_info.model_provider
        props["prompt_builder_name"] = adapter_info.prompt_builder_name

        return props
