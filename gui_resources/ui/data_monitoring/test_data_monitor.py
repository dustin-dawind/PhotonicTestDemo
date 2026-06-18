import sys
import importlib.util
from types import ModuleType
from pathlib import Path
import pandas as pd

from instruments import InstrumentRegistry

from gui_resources.ui.compound_widgets import (
    TopBanner,
    DataPlotter
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFrame,
    QMessageBox
)
from PyQt6.QtCore import (
    pyqtSlot,
    QEvent,
    QThread,
    pyqtSignal,
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
        h_divider.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)

        layout.addWidget(self.controls)
        layout.addWidget(h_divider)
        layout.addWidget(self.plotter, stretch=1)


class LiveTestDataMonitor(LiveTestDataMonitorUI):
    test_ready_to_start = pyqtSignal()
    request_stop = pyqtSignal()

    def __init__(self,
                 parent=None,
                 instruments: InstrumentRegistry = None
                 ):
        super().__init__(parent)

        self.setMinimumSize(1000, 600)

        self.test_module: ModuleType | None = None
        self.test_class = None
        self._test_thread = None

        self._active_instruments = ()

        self.device_definitions = None

        self._instrument_registry = instruments
        self.instruments = {'psu'        : instruments.psu,
                            'power_meter': instruments.power_meter,
                            'camera'     : instruments.camera
                            }

        # self.controls.start_btn.clicked.connect(self.load_device_definitions)
        self.controls.start_btn.clicked.connect(self.load_test_script)
        self.controls.start_btn.clicked.connect(self.plotter.clear_plot)

        self.instruments_started = {'psu'        : False,
                                    'power_meter': False,
                                    'camera'     : False
                                    }

        self._connected_signals = []

    def closeEvent(self, event: QEvent):
        if self.test_class is not None:
            self.stop_test()
        event.accept()

    @pyqtSlot()
    def stop_test(self):
        if self.test_class is not None:
            self.request_stop.emit()

        # self.test_class = None

    def open_warning_popup(self, message: str):
        error_popup = QMessageBox(QMessageBox.Critical,
                                  "Automation Examples - Live Data Streaming",
                                  message,
                                  QMessageBox.Ok
                                  )
        error_popup.exec_()
        self.controls.start_stop.toggle_enabled_button()

    def load_device_definitions(self):
        path = self.controls.device_definition_selector.file_path_display.text()
        if path != '':
            path = Path(path)
            self.device_definitions = pd.read_csv(path)

        return path

    @pyqtSlot()
    def load_test_script(self):
        test_script_path = self.controls.test_script_selector.file_path_display.text()
        device_definitions_path = self.load_device_definitions()
        if test_script_path != '' and device_definitions_path != '':
            path = Path(test_script_path)
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
                    self.test_class = TestClass(device_definitions=self.device_definitions)

                    for instrument in self.test_class.needed_instruments:
                        setattr(self.test_class, instrument, self.instruments[instrument])

                    self._test_thread = QThread()
                    self.test_class.moveToThread(self._test_thread)

                    self._connect_signals()
                    self.test_class.register_instruments()

    def _connect_signals(self):
        # all of these signals need to be manually disconnected because they are connected every time the script is
        # loaded, meaning they will double-up if not explicitly disconnected whenever the test script is stopped

        self.test_class.plot_data_signal[pd.Series, float, float].connect(self.plotter.append_data)
        self.test_class.plot_data_signal[pd.Series, float, float, float].connect(self.plotter.append_data)
        self.test_class.set_axes_titles_signal[str, str].connect(self.plotter.set_axes_titles)
        self.test_class.set_axes_titles_signal[str, str, str].connect(self.plotter.set_axes_titles)
        self.test_class.new_device_signal.connect(self._instrument_registry.laser_emulator.swap_device)
        self.test_class.needed_instruments_signal.connect(self.start_instruments)
        self.test_class.update_test_status_signal.connect(self.update_status)
        self.test_class.update_test_progress_signal.connect(self.update_progress_value)
        self.test_class.update_progress_bar_max.connect(self.set_progress_maximum)

        self.test_class.test_finished_signal.connect(self.stop_instruments)
        self.test_class.test_finished_signal.connect(self._test_thread.quit)

        for instrument in self.instruments:
            self.instruments[instrument].started.connect(self.instrument_started)
        self.test_ready_to_start.connect(self._test_thread.start)
        self.controls.stop_btn.clicked.connect(self.stop_test)
        self.request_stop.connect(self.test_class.request_stop)

        self._test_thread.started.connect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.started.connect(self.test_class.run_test)
        self._test_thread.started.connect(self.controls.disable_file_selection)
        self._test_thread.finished.connect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.finished.connect(self._test_thread.deleteLater)
        self._test_thread.finished.connect(self.controls.enable_file_selection)
        self._test_thread.finished.connect(self._disconnect_signals)

    def _disconnect_signals(self):
        self.test_class.plot_data_signal[pd.Series, float, float].disconnect(self.plotter.append_data)
        self.test_class.plot_data_signal[pd.Series, float, float, float].disconnect(self.plotter.append_data)
        self.test_class.set_axes_titles_signal[str, str].disconnect(self.plotter.set_axes_titles)
        self.test_class.set_axes_titles_signal[str, str, str].disconnect(self.plotter.set_axes_titles)
        self.test_class.new_device_signal.disconnect(self._instrument_registry.laser_emulator.swap_device)
        self.test_class.needed_instruments_signal.disconnect(self.start_instruments)
        self.test_class.update_test_status_signal.disconnect(self.update_status)
        self.test_class.update_test_progress_signal.disconnect(self.update_progress_value)
        self.test_class.update_progress_bar_max.disconnect(self.set_progress_maximum)
        self.test_class.test_finished_signal.disconnect(self.stop_instruments)
        self.test_class.test_finished_signal.disconnect(self._test_thread.quit)

        for instrument in self.instruments:
            self.instruments[instrument].started.disconnect(self.instrument_started)
        self.test_ready_to_start.disconnect(self._test_thread.start)
        self.controls.stop_btn.clicked.disconnect(self.stop_test)
        self.request_stop.disconnect(self.test_class.request_stop)

        self._test_thread.started.disconnect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.started.disconnect(self.test_class.run_test)
        self._test_thread.started.disconnect(self.controls.disable_file_selection)
        self._test_thread.finished.disconnect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.finished.disconnect(self._test_thread.deleteLater)
        self._test_thread.finished.disconnect(self.controls.enable_file_selection)
        self._test_thread.finished.disconnect(self._disconnect_signals)

    @pyqtSlot(object)
    def start_instruments(self, instruments: tuple[str, ...]):
        if not isinstance(instruments, tuple):
            raise TypeError(f"The 'needed_instruments' attribute must be a tuple. Offending test class: {self.test_class.test_name}")
        for instrument in instruments:
            self.instruments[instrument].start()

    @pyqtSlot()
    def stop_instruments(self):
        for instrument in self._active_instruments:
            self.instruments[instrument].stop()
        self._active_instruments = ()

    @pyqtSlot(str)
    def instrument_started(self, instrument: str):
        self.instruments_started[instrument] = True
        self._active_instruments = self._active_instruments + (instrument,)

        if self._active_instruments == self.test_class.needed_instruments:
            self.test_ready_to_start.emit()

    @pyqtSlot(int)
    def set_progress_maximum(self,
                             max_value: int
                             ):
        self.controls.set_progress_maximum(max_value)

    @pyqtSlot(int)
    def update_progress_value(self, value: int):
        self.controls.update_progress_value(value)

    @pyqtSlot(str)
    def update_status(self, status: str):
        self.controls.change_progress_status(status)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LiveTestDataMonitor()
    window.show()

    sys.exit(app.exec_())
