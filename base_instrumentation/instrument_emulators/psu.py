from copy import deepcopy
import numpy as np

from base_instrumentation.instrument_emulators.abc import (
    Setting,
    AbstractEmulator
)
from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot,
    QTimer,
    QObject,
    QReadWriteLock,
    QMutex,
)


class PSUEmulator(QObject, AbstractEmulator):
    output_changed = pyqtSignal(str)
    i_set_changed = pyqtSignal(float)
    i_current_changed = pyqtSignal(float)
    start_voltage_measurement = pyqtSignal()

    located_at = "COM10"
    settings = {"Output"       : Setting("OFF"),
                "ICurrent"     : Setting("0", readonly=True),
                "VCurrent"     : Setting("0", readonly=True),
                "ILim"         : Setting("0"),
                "VLim"         : Setting("OFF"),
                "ISet"         : Setting("0"),
                "*IDN?"        : Setting("Matthew Larkins, Emulated PSU v1.0, 11223344", readonly=True),
                "Handle?"      : Setting(located_at, readonly=True),
                "Model?"       : Setting("Emulated PSU v1.0", readonly=True),
                "Serial?"      : Setting("11223344", readonly=True),
                "Manufacturer?": Setting("Matthew Larkins", readonly=True)
                }
    default_settings = deepcopy(settings)

    settings_mutex = QReadWriteLock()
    response_mutex = QMutex()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._i_set = 0
        self._output = "OFF"

        self.poll_settings_timer = QTimer(self)
        self.poll_settings_timer.setInterval(50)
        self.poll_settings_timer.timeout.connect(self.update_output_and_current)
        self.poll_settings_timer.start()

    def query(self, command: str):
        try:
            self.settings_mutex.lockForRead()
            response = self.settings[command].value
        except KeyError:
            self.write_response_buffer(f"Invalid command: {command}")
        else:
            self.write_response_buffer(response)
        finally:
            self.settings_mutex.unlock()

    def write(self, setting: str, value: str):
        if setting not in self.settings:
            raise KeyError(f"Invalid command: {setting} {value}")
        elif self.settings[setting].readonly:
            raise IOError(f"{setting} is a read only value")
        else:
            self.settings_mutex.lockForWrite()
            self.settings[setting].value = value
            self.settings_mutex.unlock()

    def reset(self):
        self.settings_mutex.lockForWrite()
        self.settings = deepcopy(self.default_settings)
        self.settings_mutex.unlock()

    def get_response_buffer(self):
        self.response_mutex.lock()
        response = self._response
        self._response = ""
        self.response_mutex.unlock()
        return response

    def write_response_buffer(self, response: str):
        self.response_mutex.lock()
        self._response = response
        self.response_mutex.unlock()

    def update_output_and_current(self):
        self.settings_mutex.lockForRead()
        output = self.settings["Output"].value
        i_set = self.settings["ISet"].value
        self.settings_mutex.unlock()

        if output_changed := (output != self._output):
            self._output = output
            self.output_changed.emit(output)

        if output == "ON":
            i_current = i_set + np.random.normal(0, i_set * 0.02)
        else:
            i_current = 0

        self.i_current_changed.emit(i_current)

        self.settings_mutex.lockForWrite()
        self.settings["ICurrent"].value = str(i_current)
        if output_changed:
            self.settings["Output"].value = output
        if i_set != self._i_set:
            self.settings["ISet"].value = str(i_set)
        self.settings_mutex.unlock()

    def request_voltage(self):
        self.start_voltage_measurement.emit()

    @pyqtSlot(float)
    def update_voltage(self, value: float):
        self.settings_mutex.lockForWrite()
        self.settings["VCurrent"].value = str(value)
        self.settings_mutex.unlock()

