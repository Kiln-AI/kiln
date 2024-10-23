from kiln_ai.adapters.base_adapter import BasePromptBuilder


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

        if self.adapter is not None:
            adapter_instructions = self.adapter.adapter_specific_instructions()
            if adapter_instructions is not None:
                base_prompt += f"\n\n{adapter_instructions}"

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

        # TODO: tons to do on selection here. This is just a quick version
        valid_examples: list[tuple[str, str]] = []
        for run in self.task.runs():
            valid_output = None
            if run.repaired_output is not None:
                valid_output = run.repaired_output.output
            elif run.output.rating is not None and run.output.rating.is_high_quality():
                valid_output = run.output.output
            if valid_output is not None:
                valid_examples.append((run.input, valid_output))
                if len(valid_examples) >= self.__class__.example_count():
                    break

        if len(valid_examples) > 0:
            base_prompt += "# Example Outputs\n\n"
            for i, example in enumerate(valid_examples):
                base_prompt += (
                    f"## Example {i+1}\n\nInput: {example[0]}\nOutput: {example[1]}\n\n"
                )

        if self.adapter is not None:
            adapter_instructions = self.adapter.adapter_specific_instructions()
            if adapter_instructions is not None:
                base_prompt += f"# Format Instructions\n\n{adapter_instructions}\n\n"

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
