from gui_resources.ui import CloseConfirmation
import analysisfromtoml
import instruments
from .data_monitoring import (
    LiveTestDataMonitor,
    # BeamImagingMonitor
)
from PIL import Image
from pathlib import Path

from PyQt6.QtCore import (
    QEvent,
    QThread, pyqtSlot
)
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QApplication,
    QMessageBox,
)


class MainWindowUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples")
        self.setContentsMargins(5, 5, 5, 5)

        font = self.font()
        font.setPointSize(14)
        self.setFont(font)

        self.example1_btn = QPushButton("Live Test Data Monitor")
        self.example1_btn.setMinimumHeight(90)

        self.example2_btn = QPushButton("Data Analysis from Config File")
        self.example2_btn.setMinimumHeight(90)

        # self.example3_btn = QPushButton("Example 3")
        # self.example3_btn.setMinimumHeight(75)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.example1_btn)
        layout.addSpacing(5)
        layout.addWidget(self.example2_btn)
        # layout.addWidget(self.example3_btn)

        self.setFixedSize(300, self.minimumSizeHint().height())


class MainWindow(MainWindowUI):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.example1_btn.clicked.connect(self.show_example1)
        self.example2_btn.clicked.connect(self.show_example2)
        # self.example3_btn.clicked.connect(self.show_example3)

        self.instruments = instruments.InstrumentRegistry()

        self.data_monitor = None
        self.beam_imaging_monitor = None
        self.analysis = None

        self.analysis_thread = None
    def closeEvent(self, e: QEvent):
        confirmation = CloseConfirmation(parent=self)
        if confirmation.exec() == QMessageBox.StandardButton.Yes:
            self.instruments.stop_threads()
            e.accept()
            QApplication.exit()
        else:
            e.ignore()

    def show_example1(self):
        self.data_monitor = LiveTestDataMonitor(instruments=self.instruments)
        self.data_monitor.show()

    def show_example2(self):
        self.analysis_thread = QThread()
        self.analysis = analysisfromtoml.Analysis()
        self.analysis.moveToThread(self.analysis_thread)
        self.analysis_thread.started.connect(self.analysis.analysis_entry_point)
        self.analysis.figure_saved.connect(self.open_analysis_plot)
        self.analysis.figure_saved.connect(self.analysis_thread.quit)
        self.analysis.user_quit_analysis.connect(self.analysis_thread.quit)
        # self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
        self.analysis_thread.start()

    @pyqtSlot(Path)
    def open_analysis_plot(self, path_to_analysis_plot):
        img = Image.open(path_to_analysis_plot)
        img.show()

    # def show_example3(self):
    #     self.beam_imaging_monitor = BeamImagingMonitor(camera_emulator=self.instruments.camera_emulator)
    #     self.beam_imaging_monitor.show()
