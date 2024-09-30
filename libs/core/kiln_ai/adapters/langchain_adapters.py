from typing import Dict

import kiln_ai.datamodel as datamodel
from kiln_ai.adapters.prompt_builders import SimplePromptBuilder
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.messages.base import BaseMessage

from .base_adapter import BaseAdapter, BasePromptBuilder
from .ml_model_list import langchain_model_from


class LangChainPromptAdapter(BaseAdapter):
    def __init__(
        self,
        kiln_task: datamodel.Task,
        custom_model: BaseChatModel | None = None,
        model_name: str | None = None,
        provider: str | None = None,
        prompt_builder: BasePromptBuilder | None = None,
    ):
        super().__init__(kiln_task)
        if custom_model is not None:
            self.model = custom_model
        elif model_name is not None:
            self.model = langchain_model_from(model_name, provider)
        else:
            raise ValueError(
                "model_name and provider must be provided if custom_model is not provided"
            )
        if self.has_strctured_output():
            if not hasattr(self.model, "with_structured_output") or not callable(
                getattr(self.model, "with_structured_output")
            ):
                raise ValueError(
                    f"model {self.model} does not support structured output, cannot use output_json_schema"
                )
            # Langchain expects title/description to be at top level, on top of json schema
            output_schema = self.kiln_task.output_schema()
            if output_schema is None:
                raise ValueError(
                    f"output_json_schema is not valid json: {self.kiln_task.output_json_schema}"
                )
            output_schema["title"] = "task_response"
            output_schema["description"] = "A response from the task"
            self.model = self.model.with_structured_output(
                output_schema, include_raw=True
            )
        if prompt_builder is None:
            self.prompt_builder = SimplePromptBuilder(task=kiln_task, adapter=self)
        else:
            prompt_builder.adapter = self
            self.prompt_builder = prompt_builder

    def adapter_specific_instructions(self) -> str | None:
        # TODO: would be better to explicitly use bind_tools:tool_choice="task_response" here
        if self.has_strctured_output():
            return "Always respond with a tool call. Never respond with a human readable message."
        return None

    async def _run(self, input: Dict | str) -> Dict | str:
        prompt = self.prompt_builder.build_prompt()
        user_msg = self.prompt_builder.build_user_message(input)
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=user_msg),
        ]
        response = self.model.invoke(messages)
        if self.has_strctured_output():
            if (
                not isinstance(response, dict)
                or "parsed" not in response
                or not isinstance(response["parsed"], dict)
            ):
                raise RuntimeError(f"structured response not returned: {response}")
            structured_response = response["parsed"]
            return self._munge_response(structured_response)
        else:
            if not isinstance(response, BaseMessage):
                raise RuntimeError(f"response is not a BaseMessage: {response}")
            text_content = response.content
            if not isinstance(text_content, str):
                raise RuntimeError(f"response is not a string: {text_content}")
            return text_content

    def _munge_response(self, response: Dict) -> Dict:
        # Mistral Large tool calling format is a bit different. Convert to standard format.
        if (
            "name" in response
            and response["name"] == "task_response"
            and "arguments" in response
        ):
            return response["arguments"]
        return response
