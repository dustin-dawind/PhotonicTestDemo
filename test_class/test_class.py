# import time
# from collections import defaultdict
from pathlib import Path
import pandas as pd
from datetime import datetime
# from rich import print
# from rich.table import Table

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    pyqtSlot,
)


class TestClass(QObject):
    plot_data_signal = pyqtSignal([int, float, float],
                                  [int, float, float, float]
                                  )
    set_axes_titles_signal = pyqtSignal([str, str],
                                        [str, str, str]
                                        )
    new_device_signal = pyqtSignal(int)
    needed_instruments_signal = pyqtSignal(object)

    # test_started_signal = pyqtSignal(str)
    update_progress_bar_max = pyqtSignal(int)
    update_test_progress_signal = pyqtSignal(int)
    update_test_status_signal = pyqtSignal(str)
    test_finished_signal = pyqtSignal()

    def __init__(self,
                 **instruments):
        super().__init__()
        # self.measurement_times = pd.DataFrame(columns=["Wafer ID", "Field ID", "Device ID", "Time (s)"])
        self._start_time = None
        self.needed_instruments = None
        self.instruments = None
        self.user_requested_stop = False
        self.step_counter = 0

    @pyqtSlot()
    def request_stop(self):
        self.user_requested_stop = True

    def register_instruments(self):
        self.needed_instruments_signal.emit(self.needed_instruments)

    # def start_timer(self):
    #     self._start_time = time.perf_counter()
    #
    # def record_time_elapsed(self, device_num: int):
    #     if self._start_time is None:
    #         raise ValueError('Performance timer has not been started')
    #     else:
    #         self.measurement_times[device_num].append(time.perf_counter() - self._start_time)

    @pyqtSlot(dict)
    def get_instruments(self, instruments: dict):
        self.instruments = instruments

    def start_test(self, ):
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

    # def print_analytics(self):
    #     measurement_times = pd.DataFrame(self.measurement_times)
    #
    #     mean = measurement_times.values.mean() * 1000
    #     mean_err = measurement_times.values.std() * 1000
    #     total = measurement_times.values.sum()
    #
    #     print()
    #     test_analytics = Table(title='[magenta]Test Analytics[/]',
    #                            show_header=False,
    #                            show_lines=True
    #                            )
    #     test_analytics.add_row("[cyan]Avg. time per measurement: [/]",
    #                            f"[yellow]{mean: 0.1f} ms \u00B1{mean_err: 0.1f} ms[/]")
    #     test_analytics.add_row("[cyan]Total testing time: [/]",
    #                            f"[yellow]{total: 0.3f} s[/]")
    #     print(test_analytics)

    def update_test_progress(self):
        self.update_test_progress_signal.emit(self.step_counter)
        self.step_counter += 1
        QApplication.processEvents()

    def send_total_num_data_points(self, total_num_data_points: int):
        self.update_progress_bar_max.emit(total_num_data_points)

    def test_finished(self):
        self.update_test_status_signal.emit("Done!")
        self.test_finished_signal.emit()

    @staticmethod
    def save_data(data: dict[str, list[str | float]]):
        output = pd.DataFrame.from_dict(data)
        path = Path.cwd() / "test_results"

        output.to_csv(path / f'data{datetime.now().strftime("%Y%m%d-%H%M%S")}.csv', index=False)

