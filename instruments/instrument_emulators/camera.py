from copy import deepcopy
import numpy as np

from instruments.instrument_emulators.abc import (
    Setting,
    AbstractEmulator
)

from PyQt5.QtCore import (
    QObject,
    QReadWriteLock,
    pyqtSignal,
    QTimer,
    QMutex, pyqtSlot
)

class CameraEmulator(QObject, AbstractEmulator):
    frame_ready = pyqtSignal(np.ndarray)

    resolution = (640, 512)
    baseline_offset = 1000

    located_at = "COM4"
    settings = {"FrameData"    : Setting(np.zeros(resolution, dtype=np.uint16), readonly=True),
                "AutoExposure" : Setting("OFF"),
                "AutoGain"     : Setting("OFF"),
                "FrameRate"    : Setting("60"),
                "IntTime"      : Setting("0.4"),
                "Gain"         : Setting("1"),
                "Offset"       : Setting("0"),
                "*IDN?"        : Setting("Matthew Larkins, Emulated Camera v1.0, 19283746", readonly=True),
                "Handle?"      : Setting(located_at, readonly=True),
                "Model?"       : Setting("Emulated Camera v1.0", readonly=True),
                "Serial?"      : Setting("19283746", readonly=True),
                "Manufacturer?": Setting("Matthew Larkins", readonly=True)
                }
    default_settings = deepcopy(settings)

    settings_mutex = QReadWriteLock()
    response_mutex = QMutex()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_on = False

        self.data_ready = False

        self.noise_std_dev = 100
        self.sa_fwhm = 120
        self.fa_fwhm = 120

        self.beam_center = (self.resolution[0] // 2, self.resolution[1] // 2)

        self.fa_jitter = 0
        self.sa_jitter = 0

        self._frame_timer = QTimer(self)
        self._frame_timer.setInterval(1000 // int(self.settings["FrameRate"].value))  # safe because nothing else will access during init
        self._frame_timer.timeout.connect(self.generate_image)

        self._jitter_timer = QTimer(self)
        self._jitter_timer.setInterval(75)
        self._jitter_timer.timeout.connect(self.set_jitter)

    @pyqtSlot()
    def start_polling(self):
        self._frame_timer.start()
        self._jitter_timer.start()

    @pyqtSlot()
    def stop_polling(self):
        self._frame_timer.stop()
        self._jitter_timer.stop()

    def query(self, command: str):
        try:
            self.settings_mutex.lockForRead()
            response = self.settings[command].value
        except KeyError:
            self.write_response_buffer(f"Invalid command: {command}")
        else:
            self.write_response_buffer(response)
            self.data_ready = True
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

    def generate_image(self):
        self.settings_mutex.lockForRead()
        gain = float(self.settings["Gain"].value)
        offset = float(self.settings["Offset"].value)
        integration_time = float(self.settings["IntTime"].value)
        self.settings_mutex.unlock()

        raw_beam_data = self.generate_beam_data()
        background = np.random.normal(self.baseline_offset, self.noise_std_dev, self.resolution[::-1]).astype(np.uint16)

        image = (raw_beam_data * integration_time + background) * gain + offset

        image = image.clip(0, 65535).astype(np.uint16)

        self.settings_mutex.lockForWrite()
        self.settings["FrameData"].value = image
        self.settings_mutex.unlock()

    def generate_beam_data(self) -> np.ndarray:
        def gauss2d(x, y, mx, my, sx, sy):
            return 1e5 * np.exp(-((x - mx) ** 2. / (2. * sx ** 2.) + (y - my) ** 2. / (2. * sy ** 2.)))

        def as_std_dev(fwhm):
            return fwhm / (2 * np.sqrt(2 * np.log(2)))

        sa_idx = np.linspace(0, self.resolution[0] - 1, self.resolution[0])
        fa_idx = np.linspace(0, self.resolution[1] - 1, self.resolution[1])

        beam_x, beam_y = np.meshgrid(sa_idx, fa_idx)

        return gauss2d(x=beam_x,
                       y=beam_y,
                       mx=self.beam_center[0] + self.sa_jitter,
                       my=self.beam_center[1] + self.fa_jitter,
                       sx=as_std_dev(self.sa_fwhm),
                       sy=as_std_dev(self.fa_fwhm)
                       )

    def set_jitter(self):
        self.sa_jitter = np.random.normal(0, 3)
        self.fa_jitter = np.random.normal(0, 3)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import (
        QApplication
    )

    import pyqtgraph as pg

    pg.setConfigOption('useNumba', True)

    class CameraDisplay(pg.PlotWidget):
        def __init__(self):
            super().__init__()
            self.emulator = CameraEmulator()
            self.emulator.start_polling()

            self.emulator.query("FrameRate")

            self.poll_frame_data_timer = QTimer(self)
            self.poll_frame_data_timer.timeout.connect(self.poll_frame_data)
            self.poll_frame_data_timer.setInterval(1000 // int(self.emulator.get_response_buffer()))
            self.poll_frame_data_timer.start()

            self.image_item = pg.ImageItem(autoLevels=False, axisOrder='row-major')
            self.addItem(self.image_item)

            plot_item = self.getPlotItem()
            plot_item.setAspectLocked()
            plot_item.showAxes(False)

        def poll_frame_data(self):
            self.emulator.query("FrameData")

            if self.emulator.data_ready:
                image = self.emulator.get_response_buffer()
                self.image_item.setImage(image, autoLevels=False)

    app = QApplication(sys.argv)

    main_window = CameraDisplay()
    main_window.show()

    sys.exit(app.exec_())

