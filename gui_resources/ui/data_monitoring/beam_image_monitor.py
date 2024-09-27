from instruments.instrument_emulators import CameraEmulator
from gui_resources.ui.compound_widgets import (
    CameraControls,
    AllCameraPlots
)

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
)
from PyQt5.QtCore import (
    QTimer,
    pyqtSlot,
    pyqtSignal
)
import pyqtgraph as pg


class BeamImagingMonitor(QWidget):
    def __init__(self,
                 # driver_instance,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)
        # self.instr = driver_instance

        # Boilerplate stuff.
        self.setWindowTitle('Beam Imaging Monitor')
        self.resize(1200,
                    700
                    )

        # Main layout.
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(layout)

        self.controls = CameraControls()
        self.plots = AllCameraPlots()

        layout.addWidget(self.controls)
        layout.addSpacing(8)
        layout.addWidget(self.plots, stretch=1)
        layout.addSpacing(10)

    #
    # @pyqtSlot(np.ndarray, dict)
    # def update_video_display(self, pixel_data: np.ndarray[np.uint16], central_lobe_xy: dict[str, int]):
    #     self.video_feed.update_data(pixel_data,
    #                                 central_lobe_xy
    #                                 )
    #     self.subplots.linescan_plots.update_data(pixel_data,
    #                                              central_lobe_xy
    #                                              )
    #     self.subplots.histogram_plot.update_data(pixel_data)
    #
    #     QTimer.singleShot(int((1 / self.frame_rate) * 1e3), self.request_video_frame)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = BeamImagingMonitor()
    window.show()

    sys.exit(app.exec_())
