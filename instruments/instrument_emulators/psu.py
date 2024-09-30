from copy import deepcopy
import numpy as np

from instruments.instrument_emulators.abc import (
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
    output_changed_signal = pyqtSignal(str)
    i_current_changed = pyqtSignal(float)
    v_current_changed = pyqtSignal(float)

    request_voltage = pyqtSignal()
    # request_current = pyqtSignal(float)

    located_at = "COM10"
    settings = {"Output"       : Setting("OFF"),
                "ICurrent"     : Setting("0", readonly=True),
                "VCurrent"     : Setting("0", readonly=True),
                "ILim"         : Setting("0"),
                "VSet"         : Setting("0"),
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
        self._v_set = 0

        self._v_source = False

        self._poll_settings_timer = QTimer(self)
        self._poll_settings_timer.setInterval(self._timer_interval)
        self._poll_settings_timer.timeout.connect(self.update_output_and_current)

    @pyqtSlot()
    def start_polling(self):
        self._poll_settings_timer.start()

    @pyqtSlot()
    def stop_polling(self):
        self._poll_settings_timer.stop()

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
        i_set = float(self.settings["ISet"].value)
        v_set = float(self.settings["VSet"].value)
        i_lim = float(self.settings["ILim"].value)
        self.settings_mutex.unlock()

        if v_set != self._v_set:
            self._v_source = True
            self._v_set = v_set
        if i_set != self._i_set:
            self._v_source = False
            self._i_set = i_set
        if output_changed := (output != self._output):
            self._output = output
            self.output_changed_signal.emit(output)

        i_current = 0
        v_current = 0
        if output == "ON":
            if not self._v_source:
                i_current = i_set + np.random.normal(0, 1)
                self.i_current_changed.emit(i_current)
                self.request_voltage.emit()
            else:
                v_current = np.random.normal(v_set, 1e-6)
                self.v_current_changed.emit(v_current)
                # self.request_current.emit()

        self.settings_mutex.lockForWrite()
        if not self._v_source:
            self.settings["ICurrent"].value = str(i_current)
        else:
            self.settings["VCurrent"].value = str(v_current)
        if output_changed:
            self.settings["Output"].value = output
        if i_set > i_lim:
            self.settings["ISet"].value = str(i_lim)
        elif i_set != self._i_set:
            self.settings["ISet"].value = str(i_set)
        self.settings_mutex.unlock()

    @pyqtSlot(float)
    def update_voltage(self, value: float):
        self.settings_mutex.lockForWrite()
        self.settings["VCurrent"].value = str(value)
        self.settings_mutex.unlock()

    @pyqtSlot(float)
    def update_current(self, value: float):
        self.settings_mutex.lockForWrite()
        i_lim = float(self.settings["ILim"].value)
        if value > i_lim:
            value = i_lim
        self.settings["ICurrent"].value = str(value)
        self.settings_mutex.unlock()

