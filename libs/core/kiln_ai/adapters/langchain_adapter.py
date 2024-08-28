import kiln_ai.datamodel.models as models
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from langchain_groq import ChatGroq


async def test_run_prompt(prompt: str):
    model = ChatGroq(
        model="llama-3.1-8b-instant",
        stop_sequences=["<STOP>"],  # TODO: typing requires this
    )

    chunks = []
    answer = ""
    async for chunk in model.astream(prompt):
        chunks.append(chunk)
        print(chunk.content, end="", flush=True)
        # if chunk.content is instance of str:
        if isinstance(chunk.content, str):
            answer += chunk.content
    print("\nComplete\n\n")
    print(answer)
    print("\n\n")
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

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", base_prompt),
                ("human", "{input}"),
            ]
        )

        print("\n\n Prompts:\n")
        print(base_prompt)
        print("\nNext Prompt:\n")
        print(prompt, "\n\n")
        return await test_run_prompt(base_prompt)
