import numpy as np
import colorcet as cc

import pyqtgraph as pg
from PyQt5.QtCore import (
    Qt,
    pyqtSlot,
)


class DataSeries:
    def __init__(self, color):
        self._y1_data = []
        self._y2_data = []

        self.y1_series = pg.PlotDataItem(pen=pg.mkPen(color=color,
                                                      width=2,
                                                      )
                                         )
        self.y2_series = pg.PlotDataItem(pen=pg.mkPen(color=color,
                                                      width=2,
                                                      style=Qt.DashLine
                                                      )
                                         )

    def append(self, x: float, *y: float):
        y1 = None
        y2 = None

        if len(y) not in [1, 2]:
            raise ValueError(f'Expected 1 or 2 arguments, got {len(y)}')
        elif len(y) == 2:
            y1, y2 = y

        if y1 is not None:
            self._y1_data.append([x, y1])
            self._y2_data.append([x, y2])

            self.y1_series.setData(np.array(self._y1_data, dtype=np.float64))
            self.y2_series.setData(np.array(self._y2_data, dtype=np.float64))

        else:
            self._y1_data.append([x, y[0]])
            self.y1_series.setData(np.array(self._y1_data, dtype=np.float64))


class DataPlotterUI(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.plotItem.setTitle("<span style='font-size: 16pt'>Real-Time Data Monitor</span>", color='k')
        self.plotItem.showAxis('right')

        self.setBackground('w')

        self.y2_view = pg.ViewBox(parent=self.plotItem)
        self.plotItem.getAxis('right').linkToView(self.y2_view)
        self.y2_view.setXLink(self.plotItem)
        self.y2_view.setMouseEnabled(x=False, y=False)
        self.plotItem.vb.setMouseEnabled(x=False, y=False)

        self.legend = self.plotItem.addLegend(offset=(-10,-10), horSpacing=20, verSpacing=-5)
        self.legend.setLabelTextColor('k')
        self.legend.setBrush((200, 200, 200, 75))


class DataPlotter(DataPlotterUI):
    def __init__(self,
                 parent=None,
                 total_devices: int = 100,
                 ):
        super().__init__(parent)

        self.total_devices = total_devices

        self.colormap = cc.glasbey_dark

        self.all_data_series: dict[int, DataSeries] = {}
        self.active_data_series = 0

        self.plotItem.vb.sigResized.connect(self._updateViews)

    @pyqtSlot(int)
    def add_series(self, device_number: int):
        if device_number in self.all_data_series:
            return
        else:
            self.active_data_series = device_number
            new_series = DataSeries(color=self.colormap[device_number])
            self.all_data_series[device_number] = new_series

            self.addItem(new_series.y1_series)
            self.y2_view.addItem(new_series.y2_series)

    @pyqtSlot()
    def clear_plot(self):
        self.plotItem.plot(clear=True)

    @staticmethod
    def _get_title_units(title):
        match title:
            case 'Power':
                return 'mW'
            case 'Current':
                return 'mA'
            case 'Voltage':
                return 'V'
            case 'Time':
                return 's'
            case _:
                return None

    @pyqtSlot(str, str)
    @pyqtSlot(str, str, str)
    def set_axes_titles(self, x_title, *y_title: str):

        x_units = self._get_title_units(x_title)
        match len(y_title):
            case 1:
                y1_title = y_title
                y1_units = self._get_title_units(y1_title)
                y2_title = None
                y2_units = self._get_title_units(y1_title)
            case 2:
                y1_title = y_title[0]
                y1_units = self._get_title_units(y1_title)
                y2_title = y_title[1]
                y2_units = self._get_title_units(y2_title)
            case _:
                raise ValueError(f'Expected 1 or 2 arguments, got {len(y_title)}')

        if y2_title is None:
            self.y2_view.hide()
            zip_iter = zip(['bottom', 'left'],
                           [x_title, y1_title],
                           [x_units, y1_units]
                           )
            self.legend.addItem(pg.PlotDataItem(pen=pg.mkPen(color='k',
                                                             width=1
                                                             )
                                                ),
                                name=y1_title
                                )
        else:
            self.y2_view.show()
            zip_iter = zip(['bottom', 'left', 'right'],
                           [x_title, y1_title, y2_title],
                           [x_units, y1_units, y2_units]
                           )
            self.legend.addItem(pg.PlotDataItem(pen=pg.mkPen(color='k',
                                                             width=1
                                                             )
                                                ),
                                name=y1_title
                                )
            self.legend.addItem(pg.PlotDataItem(pen=pg.mkPen(color='k',
                                                             width=1,
                                                             style=Qt.DashLine
                                                             )
                                                ),
                                name=y2_title
                                )

        label_style = {'font-size': '11pt'}
        for axis, name, units in zip_iter:
            axis = self.plotItem.getAxis(axis)
            axis.setLabel(text=name,
                          units=units,
                          **label_style
                          )
            axis.setPen(black_pen := pg.mkPen(color='k'))
            axis.setTextPen(black_pen)
            axis.enableAutoSIPrefix(False)

    def change_active_data_series(self, device_number: int):
        if device_number not in self.all_data_series:
            self.add_series(device_number)
        else:
            self.active_data_series = device_number

    @pyqtSlot(bool)
    def hide_y1(self, state: bool):
        if state:
            for series in self.all_data_series.values():
                series.y1_series.hide()
        else:
            for series in self.all_data_series.values():
                series.y1_series.show()

    @pyqtSlot(bool)
    def hide_y2(self, state: bool):
        if state:
            for series in self.all_data_series.values():
                series.y2_series.hide()
        else:
            for series in self.all_data_series.values():
                series.y2_series.show()

    @pyqtSlot(int, float, float)
    @pyqtSlot(int, float, float, float)
    def append_data(self, device_num: int, x: float, *y: float):
        if device_num != self.active_data_series:
            self.change_active_data_series(device_num)
        self.all_data_series[self.active_data_series].append(x, *y)

    def _updateViews(self):
        self.y2_view.setGeometry(self.plotItem.vb.sceneBoundingRect())
        self.y2_view.linkedViewChanged(self.plotItem.vb, self.y2_view.XAxis)






