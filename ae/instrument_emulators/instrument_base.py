from abc import (
    ABC,
    abstractmethod
)

"""
Write a base class for all other instruments to inherit from.

Should include attributes for:
    * Baud rate (for "serial" connections)
    * Connection address/handle
    * Connection timeout
    * Connection handler object
    * If instrument is being tested for connection
    * If instrument is connected

Base methods for:
    * Connecting
    * Disconneting
    * Reseting
    * Getting the:
        1) serial number
        2) model number
        3) manufacturer
        4) *IDN? string
    * Anything else?
"""

class AbstractInstrument(ABC):
    @abstractmethod
    def connect(self):
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


class Camera:
    located_at = "COM4"

class OSA:
    located_at = "COM10"

class PSU:
    located_at = "COM12"

class PowerMeter:
    located_at = "COM18"