import json
from abc import ABCMeta, abstractmethod
from typing import Dict

from kiln_ai.datamodel import Task
from kiln_ai.utils.formatting import snake_case


class BasePromptBuilder(metaclass=ABCMeta):
    def __init__(self, task: Task):
        self.task = task

    @abstractmethod
    def build_prompt(self) -> str:
        pass

    # override to change the name of the prompt builder (if changing class names)
    @classmethod
    def prompt_builder_name(cls) -> str:
        return snake_case(cls.__name__)

    # Can be overridden to add more information to the user message
    def build_user_message(self, input: Dict | str) -> str:
        if isinstance(input, Dict):
            return f"The input is:\n{json.dumps(input, indent=2)}"

        return f"The input is:\n{input}"


class SimplePromptBuilder(BasePromptBuilder):
    def build_prompt(self) -> str:
        base_prompt = self.task.instruction

        # TODO: this is just a quick version. Formatting and best practices TBD
        if len(self.task.requirements) > 0:
            base_prompt += (
                "\n\nYour response should respect the following requirements:\n"
            )
            # iterate requirements, formatting them in numbereed list like 1) task.instruction\n2)...
            for i, requirement in enumerate(self.task.requirements):
                base_prompt += f"{i+1}) {requirement.instruction}\n"

        return base_prompt


class MultiShotPromptBuilder(BasePromptBuilder):
    @classmethod
    def example_count(cls) -> int:
        return 25

    def build_prompt(self) -> str:
        base_prompt = f"# Instruction\n\n{ self.task.instruction }\n\n"

        if len(self.task.requirements) > 0:
            base_prompt += "# Requirements\n\nYour response should respect the following requirements:\n"
            for i, requirement in enumerate(self.task.requirements):
                base_prompt += f"{i+1}) {requirement.instruction}\n"
            base_prompt += "\n"

        valid_examples: list[tuple[str, str]] = []
        runs = self.task.runs()

        # first pass, we look for repaired outputs. These are the best examples.
        for run in runs:
            if len(valid_examples) >= self.__class__.example_count():
                break
            if run.repaired_output is not None:
                valid_examples.append((run.input, run.repaired_output.output))

        # second pass, we look for high quality outputs (rating based)
        # Minimum is "high_quality" (4 star in star rating scale), then sort by rating
        # exclude repaired outputs as they were used above
        runs_with_rating = [
            run
            for run in runs
            if run.output.rating is not None
            and run.output.rating.value is not None
            and run.output.rating.is_high_quality()
            and run.repaired_output is None
        ]
        runs_with_rating.sort(
            key=lambda x: (x.output.rating and x.output.rating.value) or 0, reverse=True
        )
        for run in runs_with_rating:
            if len(valid_examples) >= self.__class__.example_count():
                break
            valid_examples.append((run.input, run.output.output))

        if len(valid_examples) > 0:
            base_prompt += "# Example Outputs\n\n"
            for i, example in enumerate(valid_examples):
                base_prompt += (
                    f"## Example {i+1}\n\nInput: {example[0]}\nOutput: {example[1]}\n\n"
                )

        return base_prompt


class FewShotPromptBuilder(MultiShotPromptBuilder):
    @classmethod
    def example_count(cls) -> int:
        return 4


prompt_builder_registry = {
    "simple_prompt_builder": SimplePromptBuilder,
    "multi_shot_prompt_builder": MultiShotPromptBuilder,
    "few_shot_prompt_builder": FewShotPromptBuilder,
}


# Our UI has some names that are not the same as the class names, which also hint parameters.
def prompt_builder_from_ui_name(ui_name: str) -> type[BasePromptBuilder]:
    match ui_name:
        case "basic":
            return SimplePromptBuilder
        case "few_shot":
            return FewShotPromptBuilder
        case "many_shot":
            return MultiShotPromptBuilder
        case _:
            raise ValueError(f"Unknown prompt builder: {ui_name}")
