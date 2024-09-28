import numpy as np
import rich
import cv2
from gui_resources.ui.compound_widgets.base_widgets import StartStop
from gui_resources.ui.compound_widgets import (
    CameraControls,
    AllCameraPlots
)
from instruments.instrument_emulators import CameraEmulator
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QFrame
    )
from PyQt5.QtCore import (
    QTimer,
    pyqtSlot,
    pyqtSignal,
    QEvent,
    QObject,
    QThread,
)


console = rich.console.Console()


class BeamImagingMonitorUI(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Boilerplate stuff.
        self.setWindowTitle('Beam Imaging Monitor')
        self.resize(1200,
                    700
                    )

        # Main layout.
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.start_stop = StartStop(start_text="Start Monitoring", stop_text="Stop Monitoring")
        self.controls = CameraControls()
        self.plots = AllCameraPlots()

        h_sep = QFrame()
        h_sep.setFrameShape(QFrame.HLine | QFrame.Sunken)
        h_sep.setLineWidth(3)

        h_sep_layout = QHBoxLayout()
        h_sep_layout.setContentsMargins(10, 0, 10, 0)
        h_sep_layout.addWidget(h_sep)

        start_stop_font = self.start_stop.font()
        start_stop_font.setPointSize(13)
        self.start_stop.setFont(start_stop_font)
        self.start_stop.setContentsMargins(0, 0, 10, 0)
        self.start_stop.start_btn.setContentsMargins(5, 5, 5, 5)
        self.start_stop.start_btn.setFixedSize(175, 50)
        self.start_stop.stop_btn.setContentsMargins(5, 5, 5, 5)
        self.start_stop.stop_btn.setFixedSize(175, 50)
        self.start_stop.stop_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        start_stop_layout = QVBoxLayout()
        start_stop_layout.addStretch(1)
        start_stop_layout.addWidget(self.start_stop, stretch=8)
        start_stop_layout.addStretch(1)

        top_banner_layout = QHBoxLayout()
        top_banner_layout.addWidget(self.controls)
        top_banner_layout.addLayout(start_stop_layout)

        layout.addLayout(top_banner_layout)
        layout.addSpacing(4)
        layout.addLayout(h_sep_layout)
        layout.addSpacing(4)
        layout.addWidget(self.plots, stretch=1)
        layout.addSpacing(10)


class BeamImagingMonitor(BeamImagingMonitorUI):
    update_frame_signal = pyqtSignal(np.ndarray, dict)

    closing = pyqtSignal()

    def __init__(self,
                 camera_emulator: CameraEmulator,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)

        self.instr = camera_emulator

        self.blob_detector = self.get_new_blob_detector()
        self.blob_warning_counter = 0
        self.last_known_blob_centroid = {"x": int((640 - 1) // 2),
                                         "y": int((512 - 1) // 2)
                                         }

        self.start_stop.start_btn.clicked.connect(self.plots.start_threads)
        self.start_stop.start_btn.clicked.connect(self.plots.main_plot.show_trace_markers)
        self.start_stop.start_btn.clicked.connect(self.instr.start_polling)

        self.start_stop.stop_btn.clicked.connect(self.instr.stop_polling)
        self.start_stop.stop_btn.clicked.connect(self.plots.stop_threads)
        self.start_stop.stop_btn.clicked.connect(self.plots.main_plot.hide_trace_markers)

        self.instr.started.connect(self.start_stop.toggle_enabled_button)
        self.instr.stopped.connect(self.start_stop.toggle_enabled_button)
        self.instr.frame_ready.connect(self.process_frame)

        self.update_frame_signal.connect(self.plots.main_plot.update_image)
        self.update_frame_signal.connect(self.plots.subplots.update_plots)

    @staticmethod
    def get_new_blob_detector():
        # noinspection PyUnresolvedReferences
        _params = cv2.SimpleBlobDetector_Params()

        # The blob detector converts the image into a series of binary images at different threshold levels, in
        # intervals of _params.thresholdStep. To quote a reddit thread I found on the subject - "The lower minimum
        # threshold will pick up more objects and the higher [maximum?] will pick out unique objects from an
        # otherwise seemingly blob".
        _params.minThreshold = 90
        _params.maxThreshold = 200

        _params.filterByColor = True
        _params.blobColor = 255  # Not sure if this is only going to select purely white blobs or "lighter" ones

        _params.filterByArea = True
        _params.minArea = 30
        _params.maxArea = 10000

        _params.filterByCircularity = True
        _params.minCircularity = 0.1
        _params.maxCircularity = 1

        _params.filterByInertia = True
        _params.minInertiaRatio = 0.2
        _params.maxInertiaRatio = 1

        # noinspection PyUnresolvedReferences
        return cv2.SimpleBlobDetector_create(_params)

    @pyqtSlot(np.ndarray)
    def process_frame(self, pixel_data: np.ndarray[np.uint16]):
        def find_central_lobe() -> dict[str, int]:
            # Uniformly downscale the image to uint8 for compatibility with opencv SimpleBlobDetector
            keypoints = self.blob_detector.detect((pixel_data / 257).astype(np.uint8))
            match len(keypoints):
                case 0:
                    x = self.last_known_blob_centroid["x"]
                    y = self.last_known_blob_centroid["y"]
                    return {"x": round(x), "y": round(y)}
                case 1:
                    x, y = keypoints[0].pt
                    self.last_known_blob_centroid["x"] = x
                    self.last_known_blob_centroid["y"] = y
                    return {"x": round(x), "y": round(y)}
                case _:
                    self.blob_warning_counter += 1

                    if self.blob_warning_counter % 120 == 0:
                        console.print('[bright_yellow] Warning: Too many blobs found. Either detection parameters need '
                                      'to be tuned, or a new central lobe centroid detection method must be'
                                      ' implemented[/]')

                    x = self.last_known_blob_centroid["x"]
                    y = self.last_known_blob_centroid["y"]
                    return {"x": x, "y": y}
        central_lobe_xy = find_central_lobe()

        self.update_frame_signal.emit(pixel_data, central_lobe_xy)

    # @pyqtSlot(np.ndarray, dict)
    # def update_displays(self, image: np.ndarray, central_lobe_xy: dict[str, int]):
    #     self.frame_updated.emit(image, central_lobe_xy)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = BeamImagingMonitor('')
    window.show()

    sys.exit(app.exec_())
