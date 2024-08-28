import kiln_ai.datamodel.models as models
from .ml_model_list import model_from


class LangChainBaseAdapter:
    def __init__(self, kiln_task: models.Task, model_name: str, provider: str):
        self.kiln_task = kiln_task
        self.model = model_from(model_name, provider)


async def test_run_prompt(prompt: str):
    model = model_from(model_name="llama_3_1_8b", provider="amazon_bedrock")
    model = model_from(model_name="gpt_4o_mini", provider="openai")
    model = model_from(model_name="llama_3_1_8b", provider="groq")

    chunks = []
    answer = ""
    async for chunk in model.astream(prompt):
        chunks.append(chunk)
        print(chunk.content, end="", flush=True)
        if isinstance(chunk.content, str):
            answer += chunk.content
    return answer


class ExperimentalKilnAdapter:
    def __init__(self, kiln_task: models.Task):
        self.kiln_task = kiln_task

    async def run(self):
        base_prompt = self.kiln_task.instruction

        if len(self.kiln_task.requirements()) > 0:
            base_prompt += "\n\nYou should requect the following requirements:\n"
            # iterate requirements, formatting them in numbereed list like 1) task.instruction\n2)...
            for i, requirement in enumerate(self.kiln_task.requirements()):
                base_prompt += f"{i+1}) {requirement.instruction}\n"

        base_prompt += (
            "\n\nYou should answer the following question: four plus six times 10\n"
        )

        return await test_run_prompt(base_prompt)
