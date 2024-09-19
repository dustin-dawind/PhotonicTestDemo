from instruments.instrument_emulators import CommunicationHandler
from instruments.instrument_wrappers.abc import AbstractInstrument

from PyQt5.QtCore import QObject


class Instrument(QObject, AbstractInstrument):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._connection = CommunicationHandler(parent=self)

    def _q(self, command: str) -> str:
        return self._connection.query(command)

    def _w(self, command: str):
        return self._connection.write(command)

    def connect(self, emulator: QObject):
        self._connection.connect(emulator)

    def disconnect(self):
        self._connection.disconnect()

    def reset(self):
        self._w("*RST")

    @property
    def serial(self):
        return self._q("Serial?")

    @property
    def model(self):
        return self._q("Model?")

    @property
    def manufacturer(self):
        return self._q("Manufacturer?")

    @property
    def id(self):
        return self._q("*IDN?")

    def measure(self):
        return float(self._q("Measure"))