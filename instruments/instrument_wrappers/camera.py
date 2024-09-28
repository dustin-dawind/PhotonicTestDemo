from instruments.instrument_emulators import CommunicationHandler
from instruments.instrument_wrappers.abc import AbstractInstrument
import numpy as np

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot
)


class Camera(QObject, AbstractInstrument):
    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    started = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection = CommunicationHandler(parent=parent)
        self.start_signal.connect(self._connection.start)
        self.stop_signal.connect(self._connection.stop)
        self._connection.started.connect(self._started)

    def _q(self, command: str) -> str | np.ndarray:
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
    def gain(self):
        return self._q("Gain")

    @gain.setter
    def gain(self, value):
        self._w(f"Gain {value}")

    @property
    def frame_rate(self):
        return self._q("FrameRate")

    @frame_rate.setter
    def frame_rate(self, value):
        self._w(f"FrameRate {value}")

    @property
    def offset(self):
        return self._q("Offset")

    @offset.setter
    def offset(self, value):
        self._w(f"Offset {value}")

    @property
    def integration_time(self):
        return self._q("IntTime")

    @integration_time.setter
    def integration_time(self, value):
        self._w(f"IntTime {value}")

    def get_current_frame(self) -> np.ndarray:
        return self._q("FrameData")

    def save_image(self, filename: str):
        pass

    def start(self):
        self.start_signal.emit()

    def stop(self):
        self.stop_signal.emit()

    @pyqtSlot()
    def _started(self):
        self.started.emit('camera')


if __name__ == '__main__':
    from instruments.instrument_emulators import CameraEmulator
    from PyQt5.QtWidgets import QApplication
    import sys

    def print_yes():
        print('yes')

    app = QApplication(sys.argv)

    camera = Camera()
    camera.connect(CameraEmulator())

    camera.started.connect(print_yes)

    camera.start()

    image = camera.get_current_frame()
    print(image)

    pass
