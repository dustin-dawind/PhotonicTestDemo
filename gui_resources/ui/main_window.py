from gui_resources.ui import CloseConfirmation
import analysisfromtoml
import instruments

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


    def closeEvent(self, e: QEvent):
        if not any([True if not isinstance(widget, MainWindow) else False for widget in QApplication.topLevelWidgets()]):
            e.accept()
        else:
            confirmation = CloseConfirmation(parent=self)
            if confirmation.exec_() == QMessageBox.Yes:
                e.accept()
            else:
                e.ignore()

    @staticmethod
    def show_example1():
        analysisfromtoml.launch_cmd()

    def show_example2(self):
        # TODO:
        #  * Make a live data viewer using pyqtgraph that streams real-time generated data using virtual device drivers
        pass

    def show_example3(self):
        # TODO:
        #  * Come up with a third example
        pass