from base_instrumentation.instrument_emulators import CommunicationHandler
from base_instrumentation.instruments.abc import AbstractInstrument

from PyQt5.QtCore import QObject


class Instrument(AbstractInstrument):
    def __init__(self):
        self._connection = CommunicationHandler()

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
        return self._q("Measure")