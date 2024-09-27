from gui_resources.ui.compound_widgets.base_widgets import (
    BeamTraceViewer,
    BeamHistogramPlot,
    BeamImageDisplay
)
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout
)

class SubPlots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.row_trace = BeamTraceViewer(parent=self,
                                         title="Row Trace",
                                         x_axis_length=640
                                         )
        self.col_trace = BeamTraceViewer(parent=self,
                                         title="Column Trace",
                                         x_axis_length=512
                                         )
        self.beam_histogram = BeamHistogramPlot(parent=self)

        layout.addWidget(self.row_trace)
        layout.addWidget(self.col_trace)
        layout.addWidget(self.beam_histogram)


class AllCameraPlots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.subplots = SubPlots(parent=self)
        self.main_plot = BeamImageDisplay(parent=self)

        layout.addWidget(self.main_plot, stretch=4)
        layout.addWidget(self.subplots, stretch=3)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = AllCameraPlots()
    window.show()

    sys.exit(app.exec_())
