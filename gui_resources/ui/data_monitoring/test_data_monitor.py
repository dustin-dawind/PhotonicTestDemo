import sys
import importlib.util
from types import ModuleType
from pathlib import Path

from instruments import InstrumentRegistry

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
    QEvent,
    QThread,
    QObject
)


class LiveTestDataMonitorUI(QWidget):
    def __init__(self,
                 parent=None
                 ):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples - Live Data Streaming")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.controls = TopBanner(parent=self)
        self.plotter = DataPlotter(parent=self)

        h_divider = QFrame(parent=self)
        h_divider.setFrameShape(QFrame.HLine | QFrame.Sunken)

        layout.addWidget(self.controls)
        layout.addWidget(h_divider)
        layout.addWidget(self.plotter, stretch=1)


class LiveTestDataMonitor(LiveTestDataMonitorUI):
    def __init__(self,
                 parent=None,
                 instruments: InstrumentRegistry = None
                 ):
        super().__init__(parent)

        self.test_module: ModuleType | None = None
        self.test_class = None
        self.test_thread = QThread(parent=self)

        self._instrument_registry = instruments
        self.used_instruments = {'psu': instruments.psu,
                                 'power_meter': instruments.power_meter
                                 }

        self.controls.start_btn.clicked.connect(self.load_test_script)
        for instrument in self.used_instruments:
            self.controls.start_btn.clicked.connect(self.used_instruments[instrument]._connection.emulator.start_polling)

    def closeEvent(self, event: QEvent):
        for instrument in self.used_instruments:
            self.used_instruments[instrument].disconnect()
            if self.test_class is not None:
                self.test_class.exit()
            event.accept()

    @staticmethod
    def open_warning_popup(self, message: str):
        error_popup = QMessageBox(QMessageBox.Critical,
                                  "Automation Examples - Live Data Streaming",
                                  message,
                                  QMessageBox.Ok
                                  )
        error_popup.exec_()

    @pyqtSlot()
    def load_test_script(self):
        path = self.controls.script_selector.script_path_display.text()
        if path != '':
            path = Path(path)
            try:
                test_spec = importlib.util.spec_from_file_location(path.name.split(".")[0], path)
                self.test_module = importlib.util.module_from_spec(test_spec)
                sys.modules[path.name.split(".")[0]] = self.test_module
                test_spec.loader.exec_module(self.test_module)
            except (NameError, ModuleNotFoundError):
                self.open_warning_popup("Error loading test script. Please check the script path/name and try again.")
            else:
                try:
                    TestClass = getattr(self.test_module, "Test")
                except AttributeError:
                    self.open_warning_popup("Could not find Test class in test script. Please check the script and try again.")
                else:
                    self.test_class = TestClass(num_devices=15,
                                                psu=self.used_instruments['psu'],
                                                power_meter=self.used_instruments['power_meter']
                                                )

                    # self.test_class.moveToThread(self.test_thread)
                    # self.test_thread.started.connect(self.test_class.run)
                    self.test_class.run()

    def _connect_test_signals(self):
        self.test_class.plot_data_signal.connect(self.plotter.append_data)
        self.test_class.swap_device_signal.connect(self._instrument_registry.laser_emulator.swap_device)
        self.test_class.swap_device_signal.connect(self.plotter.add_series)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = LiveTestDataMonitor()
    window.show()

    sys.exit(app.exec_())
