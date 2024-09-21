from gui_resources.ui import CloseConfirmation
import analysisfromtoml
import instruments
from gui_resources.ui.data_monitoring import LiveTestDataMonitor

from PyQt5.QtCore import (
    QEvent,
    QThread
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
        self.instruments.psu.connect(self.instruments.psu_emulator)
        self.instruments.power_meter.connect(self.instruments.power_meter_emulator)
        self.data_monitor = LiveTestDataMonitor(instruments=self.instruments)
        self.data_monitor.show()

    def show_example3(self):
        # TODO:
        #  * Come up with a third example
        pass
