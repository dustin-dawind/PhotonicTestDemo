import sys
import time
from datetime import datetime
import functools
from collections import defaultdict
from pathlib import Path
import traceback

import pandas as pd
from rich import print
from rich.table import Table

from email_notifier import (
    notify_success,
    notify_error
)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import (
    pyqtSignal,
    QObject,
    pyqtSlot,
)



file_timestamp_format = "%Y%m%d-%H%M%S"


class TestClass(QObject):
    plot_data_signal = pyqtSignal([pd.Series, float, float],
                                  [pd.Series, float, float, float]
                                  )
    set_axes_titles_signal = pyqtSignal([str, str],
                                        [str, str, str]
                                        )
    new_device_signal = pyqtSignal(pd.Series)
    needed_instruments_signal = pyqtSignal(object)

    update_progress_bar_max = pyqtSignal(int)
    update_test_progress_signal = pyqtSignal(int)
    update_test_status_signal = pyqtSignal(str)
    test_finished_signal = pyqtSignal()

    def __init__(self, test_name: str, **instruments):
        super().__init__()

        self.test_name = test_name

        self._start_time = None
        self.needed_instruments = None
        self.instruments = None
        self.user_requested_stop = False

        self.step_counter = 0
        self.DUTs = None
        self.data = defaultdict(list)

        self.filename = None
        self.save_directory = Path(Path.cwd() / "resources" / "test_results")



    @pyqtSlot()
    def request_stop(self):
        self.user_requested_stop = True

    def register_instruments(self):
        self.needed_instruments_signal.emit(self.needed_instruments)

    # def start_timer(self):
    #     self._start_time = time.perf_counter()

    @pyqtSlot(dict)
    def get_instruments(self, instruments: dict):
        self.instruments = instruments

    def run_test(self, ):
        raise NotImplementedError("This method must be overridden in a child class")

    def new_device(self, device: pd.Series):
        self.new_device_signal.emit(device)

    def send_for_plotting(self, *data):
        match len(data):
            case 3:
                self.plot_data_signal[pd.Series, float, float].emit(*data)
            case 4:
                self.plot_data_signal[pd.Series, float, float, float].emit(*data)
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
    #     total = time.perf_counter() - self._start_time
    #     mean = total / self.step_counter
    #
    #     print()
    #     test_analytics = Table(title='[magenta]Test Analytics[/]',
    #                            show_header=False,
    #                            show_lines=True
    #                            )
    #     test_analytics.add_row("[cyan]Avg. time per measurement: [/]",
    #                            f"[yellow]{mean * 1000: 0.2f} ms[/]")
    #     test_analytics.add_row("[cyan]Total testing time: [/]",
    #                            f"[yellow]{total: 0.2f} s[/]")
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

    def _save_to_generated_filename(self):
        wafers = self.DUTs["Wafer ID"].unique()
        fields = self.DUTs["Field ID"].unique()
        devices = self.DUTs["Device ID"].unique()

        if len(wafers) > 1:
            wafers = f"W{wafers[0]}-{wafers[-1]}"
        else:
            wafers = f"W{wafers[0]}"
        if len(fields) > 1:
            fields = f"F{fields[0]}-{fields[-1]}"
        else:
            fields = f"F{fields[0]}"
        if len(devices) > 1:
            devices = f"D{devices[0]}-{devices[-1]}"
        else:
            devices = f"D{devices[0]}"
        filename = f"{wafers}_{fields}_{devices}"

        full_filepath = self.save_directory / f'{filename}_{datetime.now().strftime(file_timestamp_format)}.csv'
        output = pd.DataFrame.from_dict(self.data)
        output.to_csv(full_filepath, index=False)
        print(f"\n[bright_magenta]Results saved to[/] [bright_green]'{full_filepath}'[/]")
        self.test_finished()

    def _print_time_analytics(self, start_time):
            total = time.perf_counter() - start_time
            mean = total / self.step_counter

            print()
            test_analytics = Table(title='[bright_magenta]Test Analytics[/]',
                                   show_header=False,
                                   show_lines=True
                                   )
            test_analytics.add_row("[bright_cyan]Avg. time per measurement: [/]",
                                   f"[bright_yellow]{mean * 1000:0.0f} ms[/]")
            test_analytics.add_row("[bright_cyan]Total testing time: [/]",
                                   f"[bright_yellow]{total :0.2f} s[/]")
            print(test_analytics)


def standard_test(overloaded_run_test):
    @functools.wraps(overloaded_run_test)
    def fully_wrapped_start_test(self, *args, **kwargs):
        try:
            for instrument in self.needed_instruments:
                getattr(self, instrument).reset()

            start_time = time.perf_counter()
            overloaded_run_test(self, *args, **kwargs)
            self._print_time_analytics(start_time)

            for instrument in self.needed_instruments:
                getattr(self, instrument).reset()

            self._save_to_generated_filename()

        except Exception:
            notify_error(self.test_name, traceback.format_exc())
            raise
        else:
            notify_success(self.test_name)

    return fully_wrapped_start_test












