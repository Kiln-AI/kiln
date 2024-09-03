from abc import ABCMeta, abstractmethod

from kiln_ai.datamodel.models import Task


class BaseAdapter(metaclass=ABCMeta):
    @abstractmethod
    async def run(self, input: str) -> str:
        pass


class BasePromptBuilder(metaclass=ABCMeta):
    def __init__(self, task: Task):
        self.task = task

    @abstractmethod
    def build_prompt(self, input: str) -> str:
        pass
