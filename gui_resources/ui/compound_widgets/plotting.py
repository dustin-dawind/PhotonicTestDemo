import sys
import numpy as np
import colorcet as cc

from PyQt5.QtWidgets import (
    QApplication
)
from PyQt5.QtCore import (
    Qt,
    QTimer,
    pyqtSlot,
    QObject
)

import pyqtgraph as pg


class DataSeries:
    def __init__(self, color):
        self._power_data = []
        self._voltage_data = []

        self.power_series = pg.PlotDataItem(pen=pg.mkPen(color=color,
                                                         width=2,
                                                         )
                                            )
        self.voltage_series = pg.PlotDataItem(pen=pg.mkPen(color=color,
                                                           width=2,
                                                           style=Qt.DashLine
                                                           )
                                              )

    def append(self,current, power, voltage):
        self._power_data.append([current, power])
        self._voltage_data.append([current, voltage])

        self.power_series.setData(np.array(self._power_data, dtype=np.float64))
        self.voltage_series.setData(np.array(self._voltage_data, dtype=np.float64))


class DataPlotterUI(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.plotItem.setTitle("<span style='font-size: 16pt'>Real-Time Data Monitor</span>", color='k')
        self.plotItem.showAxis('right')

        self.setBackground('w')

        self.y2_view = pg.ViewBox(parent=self.plotItem)
        # self.plotItem.scene().addItem(self.y2_view)
        self.plotItem.getAxis('right').linkToView(self.y2_view)
        self.y2_view.setXLink(self.plotItem)
        self.y2_view.setMouseEnabled(x=False, y=False)
        self.plotItem.vb.setMouseEnabled(x=False, y=False)

        label_style = {'font-size': '11pt'}
        for axis, name, units in zip(['bottom', 'left', 'right'],
                                     ['Current', 'Power', 'Voltage'],
                                     ['mA', 'mW', 'V'],
                                     ):
            axis = self.plotItem.getAxis(axis)
            axis.setLabel(text=name, units=units, **label_style)
            axis.setPen(black_pen := pg.mkPen(color='k'))
            axis.setTextPen(black_pen)
            axis.enableAutoSIPrefix(False)

        self.legend = self.plotItem.addLegend(offset=(-10,-10), horSpacing=20, verSpacing=-5)
        self.legend.setLabelTextColor('k')
        self.legend.setBrush((200, 200, 200, 75))
        self.legend.addItem(pg.PlotDataItem(pen=pg.mkPen(color='k',
                                                         width=1)
                                            ),
                            name="Power"
                            )
        self.legend.addItem(pg.PlotDataItem(pen=pg.mkPen(color='k',
                                                         width=1,
                                                         style=Qt.DashLine
                                                         )
                                            ),
                            name="Voltage"
                            )


class DataPlotter(DataPlotterUI):
    def __init__(self,
                 parent=None,
                 starting_device_number: int = 0,
                 total_devices: int = 100,
                 ):
        super().__init__(parent)

        self.total_devices = total_devices

        self.colormap = cc.glasbey_dark

        self.all_data_series: dict[int, DataSeries] = {}
        # self.add_series(starting_device_number)
        self.active_data_series = 0

        self.plotItem.vb.sigResized.connect(self._updateViews)

    # def _debug(self):
    #     self.data_counter = 0
    #     self.append_data(0, 0, 0)
    #
    #     self._laser_emulator = LaserEmulator()
    #     self._laser_emulator._psu_on = True
    #
    #     self._add_data_timer = QTimer(self)
    #     self._add_data_timer.timeout.connect(self.test_add_data)
    #     self._add_data_timer.start()

    @pyqtSlot(int)
    def add_series(self, device_number: int):
        if device_number in self.all_data_series:
            return
        else:
            self.active_data_series = device_number
            new_series = DataSeries(color=self.colormap[device_number])
            self.all_data_series[device_number] = new_series

            self.addItem(new_series.power_series)
            self.y2_view.addItem(new_series.voltage_series)

    @pyqtSlot()
    def clear_plot(self):
        self.plotItem.plot(clear=True)

    def select_data_series(self, device_number: int):
        if device_number not in self.all_data_series:
            self.add_series(device_number)
        else:
            self.active_data_series = device_number

    @pyqtSlot(bool)
    def hide_power_plot(self, state: bool):
        if state:
            for series in self.all_data_series.values():
                series.power_series.hide()
        else:
            for series in self.all_data_series.values():
                series.power_series.show()

    @pyqtSlot(bool)
    def hide_voltage_plot(self, state: bool):
        if state:
            for series in self.all_data_series.values():
                series.voltage_series.hide()
        else:
            for series in self.all_data_series.values():
                series.voltage_series.show()

    @pyqtSlot(float, float, float)
    def append_data(self, current: float, power: float, voltage: float):
        self.all_data_series[self.active_data_series].append(current, power, voltage)

    def _updateViews(self):
        self.y2_view.setGeometry(self.plotItem.vb.sceneBoundingRect())
        self.y2_view.linkedViewChanged(self.plotItem.vb, self.y2_view.XAxis)

    def test_add_data(self):
        self.data_counter += 1

        if self.data_counter % 150 != 0:
            test_current = (self.data_counter % 150) * 10
            self._laser_emulator._i_current = test_current
            self.append_data(test_current,
                             self._laser_emulator.update_power(test_current),
                             self._laser_emulator.update_voltage())
        else:
            if self.active_data_series == self.total_devices and self.data_counter % 150 == 0:
                self.add_data_timer.stop()
            else:
                self._laser_emulator.swap_device()
                self.add_series(self.active_data_series + 1)
                self.append_data(0, 0, 0)


if __name__ == "__main__":
    from instruments.instrument_emulators.laser import LaserEmulator
    app = QApplication(sys.argv)

    window = DataPlotter()
    window.show()
    window.debug()

    sys.exit(app.exec_())






