from abc import (
    ABC,
    ABCMeta,
    abstractmethod
)
from PyQt5.QtCore import QObject
import numpy as np


class Setting:
    def __init__(self,
                 value: str | np.ndarray,
                 *,
                 readonly: bool = False,
                 ):
        self.value = value
        self.readonly = readonly

    def __repr__(self):
        return repr(self.value)


class QABCMeta(ABCMeta, type(QObject)):
    pass


class AbstractEmulator(ABC, metaclass=QABCMeta):
    _timer_interval = 10

    @abstractmethod
    def query(self, command: str):
        pass

    @abstractmethod
    def write(self, setting: str, value: str):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_response_buffer(self):
        pass

    @abstractmethod
    def write_response_buffer(self, response: str):
        pass
