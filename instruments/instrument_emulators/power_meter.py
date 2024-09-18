from copy import deepcopy

import numpy as np

from instruments.instrument_emulators.abc import (
    Setting,
    AbstractEmulator
)

from PyQt5.QtCore import (
    pyqtSlot,
    QTimer,
    QObject,
    QReadWriteLock,
    QMutex,
)


class PowerMeterEmulator(QObject, AbstractEmulator):
    located_at = "COM12"
    settings = {"Measure"      : Setting("0", readonly=True),
                "*IDN?"        : Setting("Matthew Larkins, Emulated Power Meter v1.0, 87654321", readonly=True),
                "Handle?"      : Setting(located_at, readonly=True),
                "Model?"       : Setting("Emulated Power Meter v1.0", readonly=True),
                "Serial?"      : Setting("87654321", readonly=True),
                "Manufacturer?": Setting("Matthew Larkins", readonly=True),
                }
    default_settings = deepcopy(settings)

    settings_mutex = QReadWriteLock()
    response_mutex = QMutex()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.base_power_value = 0

        self.poll_power_timer = QTimer(self)
        self.poll_power_timer.setInterval(50)
        self.poll_power_timer.timeout.connect(self.update_power_reading)
        self.poll_power_timer.start()

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
        if setting in self.settings:
            raise IOError(f"{setting} is a read only value")
        else:
            raise KeyError(f"Invalid command: {setting} {value}")

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

    def update_power_reading(self):
        base_power = self.base_power_value

        current_power = base_power + np.random.normal(0, self.base_power_value * 0.02)

        self.settings_mutex.lockForWrite()
        self.settings["Measure"].value = str(current_power)
        self.settings_mutex.unlock()

    @pyqtSlot(float)
    def base_power_changed(self, value: float):
        self.base_power_value = value

