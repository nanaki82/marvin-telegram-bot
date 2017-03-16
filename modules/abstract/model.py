from abc import ABC, abstractmethod


class MarvinModel(ABC):
    @abstractmethod
    def to_dict(self):
        pass
