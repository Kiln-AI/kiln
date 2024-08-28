from abc import ABCMeta, abstractmethod

import kiln_ai.datamodel.models as models
from langchain_core.language_models.chat_models import BaseChatModel

from .ml_model_list import model_from


class BasePromptAdapter(metaclass=ABCMeta):
    def __init__(
        self,
        kiln_task: models.Task,
        custom_model: BaseChatModel | None = None,
        model_name: str | None = None,
        provider: str | None = None,
    ):
        self.kiln_task = kiln_task
        if custom_model is not None:
            self.model = custom_model
        elif model_name is not None and provider is not None:
            self.model = model_from(model_name, provider)
        else:
            raise ValueError(
                "model_name and provider must be provided if custom_model is not provided"
            )

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
