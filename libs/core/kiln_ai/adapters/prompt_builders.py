from kiln_ai.adapters.base_adapter import BasePromptBuilder


class SimplePromptBuilder(BasePromptBuilder):
    def build_prompt(self) -> str:
        base_prompt = self.task.instruction

        # TODO: this is just a quick version. Formatting and best practices TBD
        if len(self.task.requirements()) > 0:
            base_prompt += (
                "\n\nYour response should respect the following requirements:\n"
            )
            # iterate requirements, formatting them in numbereed list like 1) task.instruction\n2)...
            for i, requirement in enumerate(self.task.requirements()):
                base_prompt += f"{i+1}) {requirement.instruction}\n"

        if self.adapter is not None:
            adapter_instructions = self.adapter.adapter_specific_instructions()
            if adapter_instructions is not None:
                base_prompt += f"\n\n{adapter_instructions}"

        return base_prompt


class MultiShotPromptBuilder(BasePromptBuilder):
    def build_prompt(self) -> str:
        base_prompt = f"# Instruction\n\n{ self.task.instruction }\n\n"

        if len(self.task.requirements()) > 0:
            base_prompt += "# Requirements\n\nYour response should respect the following requirements:\n"
            for i, requirement in enumerate(self.task.requirements()):
                base_prompt += f"{i+1}) {requirement.instruction}\n"
            base_prompt += "\n"

        # TODO: tons to do on selection here. This is just a quick version
        valid_examples: list[tuple[str, str]] = []
        for example in self.task.examples():
            valid_output = None
            for output in example.outputs():
                if output.fixed_output is not None:
                    valid_output = output.fixed_output
                    break
                elif output.rating is not None and output.rating.rating >= 4:
                    valid_output = output.output
                    break
            if valid_output is not None:
                valid_examples.append((example.input, valid_output))
                if len(valid_examples) >= 10:
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
