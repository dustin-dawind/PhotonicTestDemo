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
        h_divider.setFrameShape(QFrame.HLine | QFrame.Sunken)

        layout.addWidget(self.controls)
        layout.addWidget(h_divider)
        layout.addWidget(self.plotter, stretch=1)


class LiveTestDataMonitor(LiveTestDataMonitorUI):
    test_ready_to_start = pyqtSignal()
    def __init__(self,
                 parent=None,
                 instruments: InstrumentRegistry = None
                 ):
        super().__init__(parent)

        self.test_module: ModuleType | None = None
        self.test_class = None
        self._test_thread = None

        self._active_instruments = ()

        self._instrument_registry = instruments
        self.instruments = {'psu'        : instruments.psu,
                            'power_meter': instruments.power_meter,
                            'camera'     : instruments.camera
                            }

        self.controls.start_btn.clicked.connect(self.load_test_script)
        self.controls.start_btn.clicked.connect(self.plotter.clear_plot)

        self.instruments_started = {'psu'        : False,
                                    'power_meter': False,
                                    'camera'     : False
                                    }

        self._connected_signals = []

    # def closeEvent(self, event: QEvent):
    #     self.stop_test()
    #     event.accept()

    # @pyqtSlot()
    # def stop_test(self):
    #     if self.test_class is not None:
    #
    #     self.test_class = None

    def open_warning_popup(self, message: str):
        error_popup = QMessageBox(QMessageBox.Critical,
                                  "Automation Examples - Live Data Streaming",
                                  message,
                                  QMessageBox.Ok
                                  )
        error_popup.exec_()
        self.controls.start_stop.toggle_enabled_button()

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
                    self.test_class = TestClass(self.instruments)

                    # while not all([self.instruments_started[instrument] for instrument in self.test_class.needed_instruments]):
                    #     QThread.msleep(10)


                    self._test_thread = QThread()
                    self.test_class.moveToThread(self._test_thread)

                    self._connect_signals()
                    self.test_class.register_instruments()

    def _connect_signals(self):
        self.test_class.plot_data_signal[int, float, float].connect(self.plotter.append_data)
        self.test_class.plot_data_signal[int, float, float, float].connect(self.plotter.append_data)
        self.test_class.set_axes_titles_signal[str, str].connect(self.plotter.set_axes_titles)
        self.test_class.set_axes_titles_signal[str, str, str].connect(self.plotter.set_axes_titles)
        self.test_class.new_device_signal.connect(self._instrument_registry.laser_emulator.swap_device)
        self.test_class.needed_instruments_signal.connect(self.start_instruments)
        self.test_class.test_finished_signal.connect(self.stop_instruments)
        self.test_class.test_finished_signal.connect(self._test_thread.quit)

        for instrument in self.instruments:
            self.instruments[instrument].started.connect(self.instrument_started)
        self.test_ready_to_start.connect(self._test_thread.start)
        self.controls.stop_btn.clicked.connect(self._test_thread.quit)

        self._test_thread.started.connect(self.test_class.start_test)
        self._test_thread.started.connect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.finished.connect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.finished.connect(self._test_thread.deleteLater)
        self._test_thread.finished.connect(self._disconnect_signals)
        # self._test_thread.finished.connect(self.purge_test_class)

    def _disconnect_signals(self):
        self.test_class.plot_data_signal[int, float, float].disconnect(self.plotter.append_data)
        self.test_class.plot_data_signal[int, float, float, float].disconnect(self.plotter.append_data)
        self.test_class.set_axes_titles_signal[str, str].disconnect(self.plotter.set_axes_titles)
        self.test_class.set_axes_titles_signal[str, str, str].disconnect(self.plotter.set_axes_titles)
        self.test_class.new_device_signal.disconnect(self._instrument_registry.laser_emulator.swap_device)
        self.test_class.needed_instruments_signal.disconnect(self.start_instruments)
        self.test_class.test_finished_signal.disconnect(self.stop_instruments)
        self.test_class.test_finished_signal.disconnect(self._test_thread.quit)

        for instrument in self.instruments:
            self.instruments[instrument].started.disconnect(self.instrument_started)
        self.test_ready_to_start.disconnect(self._test_thread.start)
        self.controls.stop_btn.clicked.disconnect(self._test_thread.quit)

        self._test_thread.started.disconnect(self.test_class.start_test)
        self._test_thread.started.disconnect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.finished.disconnect(self.controls.start_stop.toggle_enabled_button)
        self._test_thread.finished.disconnect(self._test_thread.deleteLater)
        # self._test_thread.finished.disconnect(self.purge_test_class)

    # def purge_test_class(self):
    #     self.test_class = None

    @pyqtSlot(object)
    def start_instruments(self, instruments: tuple[str, ...]):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LiveTestDataMonitor()
    window.show()

    sys.exit(app.exec_())
