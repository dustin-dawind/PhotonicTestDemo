from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from gui_resources.functionality.liv_window.children import LIVDataMonitor


class LivTestWindowUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples - LIV Testing")

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.liv_data_monitor = LIVDataMonitor()

        layout.addWidget(self.liv_data_monitor)


