from abc import (
    ABC,
    abstractmethod
)
from instruments.instrument_emulators.abc import QABCMeta


class AbstractInstrument(ABC, metaclass=QABCMeta):

    @abstractmethod
    def connect(self, connection):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @property
    @abstractmethod
    def serial(self):
        pass

    @property
    @abstractmethod
    def model(self):
        pass

    @property
    @abstractmethod
    def manufacturer(self):
        pass

    @property
    @abstractmethod
    def id(self):
        pass
