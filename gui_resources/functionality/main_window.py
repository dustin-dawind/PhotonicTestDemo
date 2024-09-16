from main_resources.ui import (
    CloseConfirmationUI,
    MainWindowUI,
)

import analysisfromtoml

from PyQt5.QtCore import (
    QEvent,
)
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
)


class MainWindow(MainWindowUI):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.example1_btn.clicked.connect(self.show_example1)
        self.example2_btn.clicked.connect(self.show_example2)
        self.example3_btn.clicked.connect(self.show_example3)

    def closeEvent(self, e: QEvent):
        if not any([True if not isinstance(widget, MainWindow) else False for widget in QApplication.topLevelWidgets()]):
            e.accept()
        else:
            confirmation = CloseConfirmationUI(parent=self)
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

