import time
from collections import defaultdict
import pandas as pd
from rich import print
from rich.table import Table

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    QTimer, pyqtSlot
)



class TestClass(QObject):
    plot_data_signal = pyqtSignal([int, float, float],
                                  [int, float, float, float]
                                  )
    set_axes_titles_signal = pyqtSignal([str, str], [str, str, str])
    new_device_signal = pyqtSignal(int)

    test_finished_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurement_times = defaultdict(list)
        self._start_time = None

        self._process_events_timer = QTimer()
        self._process_events_timer.timeout.connect(QApplication.processEvents)
        self._process_events_timer.start(50)

    def start_timer(self):
        self._start_time = time.perf_counter()

    def record_time_elapsed(self, device_num: int):
        if self._start_time is None:
            raise ValueError('Performance timer has not been started')
        else:
            self.measurement_times[device_num].append(time.perf_counter() - self._start_time)

    def start_test(self):
        raise NotImplementedError("This method must be overridden in a child class")

    def new_device(self, device_num: int):
        self.new_device_signal.emit(device_num)

    def send_for_plotting(self, *data):
        match len(data):
            case 3:
                self.plot_data_signal[int, float, float].emit(*data)
            case 4:
                self.plot_data_signal[int, float, float, float].emit(*data)
            case _:
                raise ValueError(f'Expected 3 or 4 arguments, got {len(data)}')

    def set_plot_axes_titles(self, x_title: str, *y_title: str):
        match len(y_title):
            case 1:
                self.set_axes_titles_signal[str, str].emit(x_title, *y_title)
            case 2:
                self.set_axes_titles_signal[str, str, str].emit(x_title, *y_title)
            case _:
                raise ValueError(f'Expected 1 or 2 arguments, got {len(y_title)}')

    def print_analytics(self):
        measurement_times = pd.DataFrame(self.measurement_times)

        mean = measurement_times.values.mean() * 1000
        mean_err = measurement_times.values.std() * 1000
        total = measurement_times.values.sum()

        print()
        test_analytics = Table(title='[magenta]Test Analytics[/]',
                               show_header=False,
                               show_lines=True
                               )
        test_analytics.add_row("[cyan]Avg. time per measurement: [/]",
                               f"[yellow]{mean: 0.1f} ms \u00B1{mean_err: 0.1f} ms[/]")
        test_analytics.add_row("[cyan]Total testing time: [/]",
                               f"[yellow]{total: 0.3f} s[/]")
        print(test_analytics)

    @pyqtSlot()
    def test_finished(self):
        self.test_finished_signal.emit()
