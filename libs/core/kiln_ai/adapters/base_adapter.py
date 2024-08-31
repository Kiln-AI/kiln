from abc import ABCMeta, abstractmethod


class BaseAdapter(metaclass=ABCMeta):
    @abstractmethod
    async def run(self, input: str) -> str:
        pass
