from kiln_ai.adapters.base_adapter import BasePromptBuilder


class SimplePromptBuilder(BasePromptBuilder):
    def build_prompt(self, input: str) -> str:
        base_prompt = self.task.instruction

        # TODO: this is just a quick version. Formatting and best practices TBD
        if len(self.task.requirements()) > 0:
            base_prompt += (
                "\n\nYour response should respectthe following requirements:\n"
            )
            # iterate requirements, formatting them in numbereed list like 1) task.instruction\n2)...
            for i, requirement in enumerate(self.task.requirements()):
                base_prompt += f"{i+1}) {requirement.instruction}\n"

        if self.adapter is not None:
            adapter_instructions = self.adapter.adapter_specific_instructions()
            if adapter_instructions is not None:
                base_prompt += f"\n\n{adapter_instructions}\n\n"

        # TODO: should be another message, not just appended to prompt
        base_prompt += f"\n\nThe input is:\n{input}"
        return base_prompt
