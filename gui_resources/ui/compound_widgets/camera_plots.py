import numpy as np
import rich
from PyQt5.QtCore import (
    pyqtSlot,
    QThread,
    pyqtSignal
    )

from gui_resources.ui.compound_widgets.base_widgets import (
    BeamTraceViewer,
    BeamHistogramPlot,
    BeamImageDisplay
)
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

console = rich.console.Console()


class SubPlots(QWidget):
    update_row_trace = pyqtSignal(np.ndarray)
    update_col_trace = pyqtSignal(np.ndarray)
    update_beam_histogram = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.row_trace = BeamTraceViewer(parent=self,
                                         title="Row Trace",
                                         x_axis_length=640
                                         )
        self.row_trace_thread = QThread(parent=parent)
        self.row_trace.moveToThread(self.row_trace_thread)

        self.col_trace = BeamTraceViewer(parent=self,
                                         title="Column Trace",
                                         x_axis_length=512
                                         )
        self.col_trace_thread = QThread(parent=parent)
        self.col_trace.moveToThread(self.col_trace_thread)

        self.beam_histogram = BeamHistogramPlot(parent=self)
        self.beam_histogram_thread = QThread(parent=parent)
        self.beam_histogram.moveToThread(self.beam_histogram_thread)

        layout.addWidget(self.row_trace)
        layout.addWidget(self.col_trace)
        layout.addWidget(self.beam_histogram)

        self.update_row_trace.connect(self.row_trace.update_data)
        self.update_col_trace.connect(self.col_trace.update_data)
        self.update_beam_histogram.connect(self.beam_histogram.update_data)

    @pyqtSlot(np.ndarray, dict)
    def update_plots(self, image_data: np.ndarray[np.uint16], central_lobe_data: dict[str, int]):
        try:
            row_data = image_data[central_lobe_data["y"], :]
            column_data = image_data[:, central_lobe_data["x"]]
        except IndexError:
            console.print("[bright_red]An error occurred while trying to update row/column linescans."
                          f"\n\ncentral lobe coordinates: x={central_lobe_data['x']} y={central_lobe_data['y']}[/]")
            raise
        else:
            self.update_beam_histogram.emit(image_data)
            self.update_row_trace.emit(row_data)
            self.update_col_trace.emit(column_data)


class AllCameraPlots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.subplots = SubPlots(parent=self)

        self.main_plot = BeamImageDisplay(parent=self)
        self.main_plot_thread = QThread(parent=parent)
        self.main_plot.moveToThread(self.main_plot_thread)

        layout.addWidget(self.main_plot, stretch=4)
        layout.addWidget(self.subplots, stretch=3)

    @pyqtSlot()
    def start_threads(self):
        self.main_plot_thread.start()
        self.subplots.row_trace_thread.start()
        self.subplots.col_trace_thread.start()
        self.subplots.beam_histogram_thread.start()

    @pyqtSlot()
    def stop_threads(self):
        self.main_plot_thread.quit()
        self.subplots.row_trace_thread.quit()
        self.subplots.col_trace_thread.quit()
        self.subplots.beam_histogram_thread.quit()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = AllCameraPlots()
    window.show()

    sys.exit(app.exec_())
