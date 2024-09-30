import json
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Dict

from kiln_ai.datamodel import (
    Example,
    ExampleOutput,
    ExampleOutputSource,
    ExampleSource,
    Task,
)
from kiln_ai.datamodel.json_schema import validate_schema
from kiln_ai.utils.config import Config


@dataclass
class AdapterInfo:
    adapter_name: str
    model_name: str
    model_provider: str


class BaseAdapter(metaclass=ABCMeta):
    def __init__(self, kiln_task: Task):
        self.kiln_task = kiln_task
        self.output_schema = self.kiln_task.output_json_schema
        self.input_schema = self.kiln_task.input_json_schema

    async def invoke(
        self, input: Dict | str, input_source: ExampleSource = ExampleSource.human
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

        # Save the example and output
        if Config.shared().autosave_examples:
            self.save_example(input, input_source, result)

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

    # create an example and example output
    def save_example(
        self, input: Dict | str, input_source: ExampleSource, output: Dict | str
    ) -> Example:
        # Convert input and output to JSON strings if they are dictionaries
        input_str = json.dumps(input) if isinstance(input, dict) else input
        output_str = json.dumps(output) if isinstance(output, dict) else output

        # Check for existing example with matching parent.id, input, and source
        existing_example = next(
            (
                example
                for example in self.kiln_task.examples()
                if (parent_task := example.parent_task()) is not None
                and parent_task.id == self.kiln_task.id
                and example.input == input_str
                and example.source == input_source
            ),
            None,
        )

        if existing_example:
            example = existing_example
        else:
            example = Example(
                parent=self.kiln_task,
                input=input_str,
                source=input_source,
            )
            example.save_to_file()

        # Check for existing ExampleOutput with matching parent.id, input, and source
        existing_output = next(
            (
                output
                for output in example.outputs()
                if (parent_example := output.parent_example()) is not None
                and parent_example.id == example.id
                and output.output == output_str
            ),
            None,
        )

        if existing_output:
            return example

        # Create a new ExampleOutput for the existing or new Example
        example_output = ExampleOutput(
            parent=example,
            output=output_str,
            source=ExampleOutputSource.synthetic,
            source_properties={"creator": Config.shared().user_id},
        )
        example_output.save_to_file()
        return example


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
