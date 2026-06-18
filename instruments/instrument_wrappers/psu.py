from instruments.instrument_emulators import CommunicationHandler
from instruments.instrument_wrappers.abc import AbstractInstrument

from PyQt6.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot
)


class PSU(QObject, AbstractInstrument):
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    started = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection = CommunicationHandler(parent=parent)
        self.start_signal.connect(self._connection.start)
        self.stop_signal.connect(self._connection.stop)
        self._connection.started.connect(self._started)

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

    @property
    def output(self):
        return self._q("Output")

    @output.setter
    def output(self, value):
        if (value := value.upper()) in ["ON", "OFF"]:
            self._w(f"Output {value}")
        else:
            raise ValueError(f"Value must be 'ON' or 'OFF'. Got: {value}")

    @property
    def i_lim(self):
        return float(self._q("ILim"))

    @i_lim.setter
    def i_lim(self, value):
        self._w(f"ILim {value}")

    # @property
    # def v_lim(self):
    #     return self._q("VLim")
    #
    # @v_lim.setter
    # def v_lim(self, value):
    #     self._w(f"VLim {value}")

    @property
    def i_setpoint(self):
        return float(self._q("ISet"))

    @i_setpoint.setter
    def i_setpoint(self, value):
        self._w(f"ISet {value}")

    @property
    def v_setpoint(self):
        return float(self._q("VSet"))

    @v_setpoint.setter
    def v_setpoint(self, value):
        self._w(f"VSet {value}")

    def measure_current(self):
        return float(self._q("ICurrent"))

    def measure_voltage(self):
        return float(self._q("VCurrent"))

    def start(self):
        self.start_signal.emit()

    def stop(self):
        self.stop_signal.emit()

    @pyqtSlot()
    def _started(self):
        self.started.emit('psu')
