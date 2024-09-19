import importlib.util
from types import ModuleType
from pathlib import Path

from gui_resources.ui.compound_widgets import (
    TopBanner,
    DataPlotter
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFrame,
    QMessageBox
)
from PyQt5.QtCore import (
    pyqtSlot,
    )


class LiveTestDataMonitorUI(QWidget):
    def __init__(self,
                 parent=None
                 ):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples - Live Data Streaming")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.controls = TopBanner()
        self.liv_data_monitor = DataPlotter()

        h_divider = QFrame()
        h_divider.setFrameShape(QFrame.HLine | QFrame.Sunken)

        layout.addWidget(self.controls)
        layout.addWidget(h_divider)
        layout.addWidget(self.liv_data_monitor, stretch=1)


class LiveTestDataMonitor(LiveTestDataMonitorUI):
    def __init__(self,
                 parent=None,
                 **instruments
                 ):
        super().__init__(parent)

        self.controls.start_btn.clicked.connect(self.load_test_script)

        self.test_module: ModuleType | None = None
        self.TestClass = None
        self.instruments = instruments

    
    @pyqtSlot()
    def load_test_script(self):
        path = Path(self.controls.script_selector.script_path_display.text())
        try:
            test_spec = importlib.util.spec_from_file_location(path.name.split(".")[0], path)
            self.test_module = importlib.util.module_from_spec(test_spec)
            sys.modules[path.name.split(".")[0]] = self.test_module
            test_spec.loader.exec_module(self.test_module)
        except (NameError, ModuleNotFoundError):
            error_popup = QMessageBox(QMessageBox.Critical,
                                      "Automation Examples - Live Data Streaming",
                                      "Error loading test script. Please check the script path and try again.",
                                      QMessageBox.Ok
                                      )
            error_popup.exec_()

        try:
            self.TestClass = getattr(self.test_module, "Test")
        except AttributeError:
            error_popup = QMessageBox(QMessageBox.Critical,
                                      "Automation Examples - Live Data Streaming",
                                      "Could not find Test class in test script. Please check the script and try again.",
                                      QMessageBox.Ok
                                      )
            error_popup.exec_()
        else:
            self.TestClass(num_devices=15,
                           psu=self.instruments['psu'],
                           power_meter=self.instruments['power_meter']
                           ).run()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = LiveTestDataMonitor()
    window.show()

    sys.exit(app.exec_())
