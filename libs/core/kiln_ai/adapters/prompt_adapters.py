import kiln_ai.datamodel.models as models
from .ml_model_list import model_from
from abc import ABCMeta, abstractmethod


class BasePromptAdapter(metaclass=ABCMeta):
    def __init__(self, kiln_task: models.Task, model_name: str, provider: str):
        self.kiln_task = kiln_task
        self.model = model_from(model_name, provider)

    @abstractmethod
    def build_prompt(self) -> str:
        pass

    # TODO: don't just append input to prompt
    async def run(self, input: str) -> str:
        # TODO cleanup
        prompt = self.build_prompt()
        prompt += f"\n\n{input}"
        chunks = []
        answer = ""
        async for chunk in self.model.astream(prompt):
            chunks.append(chunk)
            print(chunk.content, end="", flush=True)
            if isinstance(chunk.content, str):
                answer += chunk.content
        return answer


class SimplePromptAdapter(BasePromptAdapter):
    def build_prompt(self) -> str:
        base_prompt = self.kiln_task.instruction

        if len(self.kiln_task.requirements()) > 0:
            base_prompt += "\n\nYou should requect the following requirements:\n"
            # iterate requirements, formatting them in numbereed list like 1) task.instruction\n2)...
            for i, requirement in enumerate(self.kiln_task.requirements()):
                base_prompt += f"{i+1}) {requirement.instruction}\n"

        return base_prompt
