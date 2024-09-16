from abc import (
    ABC,
    abstractmethod
)


class AbstractInstrument(ABC):

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
