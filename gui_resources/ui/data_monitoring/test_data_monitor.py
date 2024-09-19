import importlib
from types import ModuleType

from gui_resources.ui.compound_widgets import (
    TopBanner,
    LIVDataMonitor
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFrame,
)
from PyQt5.QtCore import (
    pyqtSlot,
    pyqtSignal
    )



class LiveTestDataMonitorUI(QWidget):
    def __init__(self, parent=None, instruments=None):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples - Live Data Streaming")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.controls = TopBanner()
        self.liv_data_monitor = LIVDataMonitor()

        h_divider = QFrame()
        h_divider.setFrameShape(QFrame.HLine | QFrame.Sunken)

        layout.addWidget(self.controls)
        layout.addWidget(h_divider)
        layout.addWidget(self.liv_data_monitor, stretch=1)


class LiveTestDataMonitor(LiveTestDataMonitorUI):
    def __init__(self, parent=None, instruments=None):
        super().__init__(parent, instruments)

        self.controls.start_btn.connect(self.load_test_script)

        self.test_script: ModuleType | None = None

    
    @pyqtSlot()
    def load_test_script():
        # TODO: Implement function that takes a filepath as a parameter, loads a script as a module, and
        #  executes it. It should be able to receive and reroute signals as the script executes so that they can be
        #  used to update the live data monitor.
        #   => The script should be loaded as a module so that the script loader can connect appropriate emitted signals
        path = self.controls.script_selector.script_path_display.text()
        # importlib.


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = LivTestWindowUI()
    window.show()

    sys.exit(app.exec_())
