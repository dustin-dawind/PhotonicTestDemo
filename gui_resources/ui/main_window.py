from gui_resources.ui import CloseConfirmation
import analysisfromtoml
import instruments
from .data_monitoring import (
    LiveTestDataMonitor,
    BeamImagingMonitor
)

from PyQt5.QtCore import (
    QEvent,
)
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QApplication,
    QMessageBox,
)


class MainWindowUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        """
        self.setWindowTitle(' ')
        logo_path = str(current_directory.parent / 'pictures/fp_logo_ico.png')
        icon = QIcon(str(logo_path))
        self.setWindowIcon(icon)
        """
        self.setWindowTitle("Automation Examples")

        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        self.example1_btn = QPushButton("Example 1")
        self.example1_btn.setMinimumHeight(75)

        self.example2_btn = QPushButton("Example 2")
        self.example2_btn.setMinimumHeight(75)

        self.example3_btn = QPushButton("Example 3")
        self.example3_btn.setMinimumHeight(75)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.example1_btn)
        layout.addWidget(self.example2_btn)
        layout.addWidget(self.example3_btn)

        self.setFixedSize(300, self.minimumSizeHint().height())


class MainWindow(MainWindowUI):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.example1_btn.clicked.connect(self.show_example1)
        self.example2_btn.clicked.connect(self.show_example2)
        self.example3_btn.clicked.connect(self.show_example3)

        self.instruments = instruments.InstrumentRegistry()

        self.data_monitor = None
        self.beam_imaging_monitor = None

    def closeEvent(self, e: QEvent):
        confirmation = CloseConfirmation(parent=self)
        if confirmation.exec_() == QMessageBox.Yes:
            self.instruments.stop_threads()
            e.accept()
            QApplication.exit()
        else:
            e.ignore()

    @staticmethod
    def show_example1():
        analysisfromtoml.launch_cmd()

    def show_example2(self):
        self.data_monitor = LiveTestDataMonitor(instruments=self.instruments)
        self.data_monitor.show()

    def show_example3(self):
        self.beam_imaging_monitor = BeamImagingMonitor(driver_instance=self.instruments.camera)
        self.beam_imaging_monitor.show()
