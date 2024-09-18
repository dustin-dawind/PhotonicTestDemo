from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFrame,
)
from gui_resources.ui.compound_widgets import (
    TopBarUI,
    LIVDataMonitor
)


class LivTestWindowUI(QWidget):
    def __init__(self, parent=None, instruments=None):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples - LIV Testing")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.controls = TopBarUI()
        self.liv_data_monitor = LIVDataMonitor()

        h_divider = QFrame()
        h_divider.setFrameShape(QFrame.HLine | QFrame.Sunken)

        layout.addWidget(self.controls)
        layout.addWidget(h_divider)
        layout.addWidget(self.liv_data_monitor, stretch=1)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = LivTestWindowUI()
    window.show()

    sys.exit(app.exec_())
