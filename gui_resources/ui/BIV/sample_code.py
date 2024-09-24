from functools import partial
from typing import Literal

import cv2
import numpy as np

import warnings

# Importing third party packages.
from PyQt5.QtCore import (
    pyqtSlot,
    pyqtSignal,
    QTimer,
    QThread,
    Qt,
    QPointF,
    )
from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QLabel,
    QFrame,
    QComboBox,
    QCheckBox,
    QGridLayout,
    QMessageBox,
    )
from PyQt5.QtGui import (
    QPen,
    QColor,
    )
import pyqtgraph as pg

# Import your own packages
import freedomlib as fl
from freedomlib.interfaces.helpers.messageboxes import MessageBoxOkCancel
from freedomlib.interfaces.freedom_test.monitors.beam_profiling import common


MAX_INT_16 = 2**16

pg.setConfigOption('useNumba', True)

empty_object = common.EmptyObject()


class MainPlotViewer(pg.PlotWidget):
    def __init__(self,
                 resolution: tuple[int, int] = (640, 512),
                 *args,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.setGeometry(QRect(30, 30, *resolution))
        self.setBackground('gray')
        self.setAspectLocked(True)

        disable_extra_context_menu_options(self)
        self.setContextMenuActionVisible('Grid', False)

        self.getPlotItem().hideAxis('left')
        self.getPlotItem().hideAxis('bottom')


class SubPlotViewer(pg.PlotWidget):
    _PositionTypes = Literal['Pixels', 'Index', 'µm', 'mm']

    _BgColors = Literal['k', 'black', 'w', 'white']

    def __init__(self, *args,
                 x_axis_length: int = 640,
                 y_axis_length: int | None = 1,
                 plot_title: str = '',
                 position_type: _PositionTypes = 'Pixels',
                 center_x_at_zero: bool = False,
                 init_with_noise: bool = True,
                 **kwargs):
        super().__init__(*args, **kwargs)

        if position_type not in (allowed_type := get_args(self._PositionTypes)):
            raise ValueError(f"Position type must be one of {allowed_type}")
        else:
            position_axis_title = f'Position ({position_type})'

        self.plot_area: pg.PlotDataItem = self.plot(pen=(150, 150, 150))
        self.init_with_noise = init_with_noise

        if self.init_with_noise is True:
            noise_max = y_axis_length if y_axis_length is not None else 5000

            if noise_max == 1 and center_x_at_zero is True:
                mean = 0
                fwhm = 120
                std = fwhm / (2 * np.sqrt(2 * np.log(2)))
                x = np.linspace(-x_axis_length // 2, x_axis_length // 2, x_axis_length + 1)
                init_data = stats.norm.pdf(x, mean, std)
                init_data = init_data / np.max(init_data)
                self.plot_area.setData(x=x, y=init_data)

            else:
                init_data = np.random.randint(0, noise_max, x_axis_length)
                self.plot_area.setData(init_data)

        self._plot_title = plot_title

        if center_x_at_zero:
            x_max = x_axis_length // 2
            self.setLimits(xMin=-x_max,
                           xMax=x_max,
                           yMin=0,
                           yMax=y_axis_length,
                           )
        else:
            self.setLimits(xMin=0,
                           xMax=x_axis_length,
                           yMin=0,
                           yMax=y_axis_length,
                           )

        self.plot_item: pg.PlotItem = self.getPlotItem()
        self.plot_item.setTitle(self._plot_title)
        self.plot_item.setLabel('left', 'Intensity (a.u.)')
        self.plot_item.setLabel('bottom', position_axis_title)

        self.x_axis: pg.AxisItem = self.getAxis('bottom')
        self.x_axis.showLabel()

        self.y_axis: pg.AxisItem = self.getAxis('left')
        self.y_axis.showLabel()

        self.disableAutoRange(axis=pg.ViewBox.XYAxes)
        self.setAntialiasing(True)

    def showEvent(self, event: QEvent):
        super().showEvent(event)
        self._fit_axes_to_view()

    def resizeEvent(self, event: QEvent):
        super().resizeEvent(event)
        self._fit_axes_to_view()

    def _fit_axes_to_view(self, padding: float = 0.05):
        scene_rect = self.sceneRect()

        width = scene_rect.width() * (1 + padding)
        height = scene_rect.height()
        center = scene_rect.center()
        zoom_rect = QRectF(center.x() - width / 2, center.y() - height / 2, width, height)

        self.fitInView(zoom_rect)

    def set_background_color(self, color: _BgColors = 'k'):
        """Sets the background color of the plot

        This will automatically update the foreground colors as well to maintain contrast

        allowed background colors are 'k'/'black' & 'w'/'white'

        Parameters
        ----------
        color : str, optional
            The color to set the background to, by default 'k'
        """

        match color:
            case bg_color if bg_color not in get_args(self._BgColors):
                raise ValueError(f"Background color must be one of {get_args(self._BgColors)}. Got {bg_color}")

            case _:
                # Note that `color` is still bound to `bg_color` via the previous case statement

                # Set the background color
                self.setBackground(bg_color)

                # Set all foreground colors with contrasting color
                contrast_color = 'd' if bg_color == 'k' else 'k'

                y_axis = self.plot_item.axes['left']['item']
                x_axis = self.plot_item.axes['bottom']['item']

                y_axis.setPen(contrast_color)
                y_axis.setTextPen(contrast_color)

                x_axis.setPen(contrast_color)
                x_axis.setTextPen(contrast_color)

                self.plot_item.setTitle(self._plot_title, color=contrast_color)

                # if self.init_with_noise is True:
                #     self.plot_area.setPen(contrast_color)

    def set_foreground_color(self, color: str):
        pass


class MonitorSetupInfo(QFrame):
    """GUI section for user to select the camera from which to display camera feed and to modify camera settings."""
    initialize_selected_instrument = pyqtSignal(dict)
    update_main_window_frame_rate = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --------------------------------------
        # Look and layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)

        # --------------------------------------
        self.start_stop = common.StartStop()
        self.instrument_selection = AttolloInstrumentSelection()
        instr_selection_and_start_stop = QVBoxLayout()

        instr_selection_and_start_stop.addLayout(self.instrument_selection)
        instr_selection_and_start_stop.addLayout(self.start_stop)

        self.layout.addLayout(instr_selection_and_start_stop)
        self.layout.addSpacing(20)

        self.instruments = self.instrument_selection.instruments

        # --------------------------------------
        # General settings
        self.attollo_settings_frame = QFrame()
        self.attollo_settings_frame.setFrameShape(QFrame.Box)
        self.attollo_settings_frame.setObjectName("cam_settings")
        self.attollo_settings_frame.setStyleSheet("QFrame#cam_settings {border: 1px solid black; border-radius: 3px;}")

        instrument_settings_layout = QGridLayout()

        self.advanced_settings = AdvancedSettings()
        self.advanced_settings_btn = QPushButton('Advanced Settings')
        self.trigger_toggle = QCheckBox()
        self.frame_rate = QLineEdit('')
        common.fix_lineedit_width(self.frame_rate)

        instrument_settings_layout.addWidget(QLabel('Trigger Mode:'), 1, 0, 1, 1, Qt.AlignRight)
        instrument_settings_layout.addWidget(self.trigger_toggle, 1, 1, 1, 1, Qt.AlignCenter)
        instrument_settings_layout.addWidget(QLabel('Frame Rate (Hz):'), 2, 0, 1, 1, Qt.AlignRight)
        instrument_settings_layout.addWidget(self.frame_rate, 2, 1, 1, 1)
        instrument_settings_layout.addWidget(self.advanced_settings_btn, 3, 0, 1, 2, Qt.AlignCenter)

        # Slider Text Box Headers
        instrument_settings_layout.addWidget(QLabel("Min"), 0, 4, 1, 1, Qt.AlignCenter)
        instrument_settings_layout.addWidget(QLabel("Max"), 0, 8, 1, 1, Qt.AlignCenter)
        instrument_settings_layout.addWidget(QLabel("Set"), 0, 9, 1, 1, Qt.AlignCenter)

        # Integration time
        self.integration_min = QLineEdit('0.1')
        self.integration_min.setAlignment(Qt.AlignCenter)
        self.integration_max = QLineEdit('10')
        self.integration_max.setAlignment(Qt.AlignCenter)
        self.integration_time_slider = common.FloatSlider(precision=2)
        self.integration_display = QLineEdit('')
        self.integration_display.setAlignment(Qt.AlignCenter)

        self.integration_time_slider.setRange(0.1, 10)

        instrument_settings_layout.addWidget(QLabel('Integration Time (ms):'), 1, 3, 1, 1, Qt.AlignRight)
        instrument_settings_layout.addWidget(self.integration_min, 1, 4, 1, 1)
        instrument_settings_layout.addWidget(self.integration_time_slider, 1, 5, 1, 3)
        instrument_settings_layout.addWidget(self.integration_max, 1, 8, 1, 1)
        instrument_settings_layout.addWidget(self.integration_display, 1, 9, 1, 1)
        common.fix_lineedit_width(self.integration_min)
        common.fix_lineedit_width(self.integration_max)
        common.fix_lineedit_width(self.integration_display)

        # Gain
        self.gain_min = QLineEdit('1')
        self.gain_min.setAlignment(Qt.AlignCenter)
        self.gain_max = QLineEdit('3')
        self.gain_max.setAlignment(Qt.AlignCenter)
        self.gain_display = QLineEdit('')
        self.gain_display.setAlignment(Qt.AlignCenter)
        self.gain_slider = common.FloatSlider(precision=2)
        self.gain_slider.setRange(1, 3)

        instrument_settings_layout.addWidget(QLabel('Gain:'), 2, 3, 1, 1, Qt.AlignRight)
        instrument_settings_layout.addWidget(self.gain_min, 2, 4, 1, 1)
        instrument_settings_layout.addWidget(self.gain_slider, 2, 5, 1, 3)
        instrument_settings_layout.addWidget(self.gain_max, 2, 8, 1, 1)
        instrument_settings_layout.addWidget(self.gain_display, 2, 9, 1, 1)
        common.fix_lineedit_width(self.gain_min)
        common.fix_lineedit_width(self.gain_max)
        common.fix_lineedit_width(self.gain_display)

        # Offset
        self.offset_min = QLineEdit('-10000')
        self.offset_min.setAlignment(Qt.AlignCenter)
        self.offset_max = QLineEdit('10000')
        self.offset_max.setAlignment(Qt.AlignCenter)
        self.offset_display = QLineEdit('')
        self.offset_display.setAlignment(Qt.AlignCenter)
        self.offset_slider = common.FloatSlider(precision=0)
        self.offset_slider.setRange(-10000, 10000)
        self.offset_slider.setValue(0)

        instrument_settings_layout.addWidget(QLabel('Offset:'), 3, 3, 1, 1, Qt.AlignRight)
        instrument_settings_layout.addWidget(self.offset_min, 3, 4, 1, 1)
        instrument_settings_layout.addWidget(self.offset_slider, 3, 5, 1, 3)
        instrument_settings_layout.addWidget(self.offset_max, 3, 8, 1, 1)
        instrument_settings_layout.addWidget(self.offset_display, 3, 9, 1, 1)
        common.fix_lineedit_width(self.offset_min)
        common.fix_lineedit_width(self.offset_max)
        common.fix_lineedit_width(self.offset_display)

        # Assembling the instrument_settings_container layout and sub-layouts
        v_line = QFrame()
        v_line.setFrameShape(QFrame.VLine)

        settings_title = QLabel('Attollo-specific Settings:')
        title_font = settings_title.font()
        title_font.setUnderline(True)
        settings_title.setFont(title_font)

        instrument_settings_layout.addWidget(settings_title, 0, 0, 1, 2, Qt.AlignCenter)
        instrument_settings_layout.addWidget(v_line, 1, 2, -1, 1, Qt.AlignHCenter)

        instrument_settings_layout.setColumnStretch(5, 1)
        instrument_settings_layout.setColumnStretch(6, 1)
        instrument_settings_layout.setColumnStretch(7, 1)

        self.attollo_settings_frame.setLayout(instrument_settings_layout)

        self.layout.addWidget(self.attollo_settings_frame)

        self.attollo_settings_frame.setEnabled(False)

        self._current_frame_rate = None
        self._current_integration_time = None
        self._current_gain = None
        self._current_offset = None

        self.absolute_slider_bounds = {'offset':          {'min': None,
                                                           'max': None
                                                           },
                                       'gain':            {'min': None,
                                                           'max': None
                                                           },
                                       'integration':     {'min': None,
                                                           'max': None
                                                           }
                                       }
        self.previous_slider_bounds = {'offset':          {'min': "0.1",
                                                           'max': "10"
                                                           },
                                       'gain':            {'min': "1",
                                                           'max': "3"
                                                           },
                                       'integration':     {'min': "-10000",
                                                           'max': "10000"
                                                           }
                                       }

        # Connect signals
        # Connect combobox to enable/disable relevant widgets
        self.instruments.currentTextChanged.connect(self.displayed_instr_changed)
        # Connect trigger toggle to camera trigger mode setting
        self.trigger_toggle.stateChanged.connect(self.changed_trigger_mode)
        # Connect frame rate to camera frame rate setting
        self.frame_rate.editingFinished.connect(self.changed_frame_rate)
        # Connect all slider text boxes to relevant sliders
        self.integration_max.editingFinished.connect(partial(self.slider_bounds_changed,
                                                             min_or_max="max",
                                                             setting='integration',
                                                             display_box=self.integration_max,
                                                             slider_widget=self.integration_time_slider
                                                             )
                                                     )
        self.integration_min.editingFinished.connect(partial(self.slider_bounds_changed,
                                                             min_or_max="min",
                                                             setting='integration',
                                                             display_box=self.integration_min,
                                                             slider_widget=self.integration_time_slider
                                                             )
                                                     )
        self.integration_time_slider.floatValueChanged.connect(partial(self.display_new_slider_value,
                                                                       display_box=self.integration_display,
                                                                       slider_widget=self.integration_time_slider
                                                                       )
                                                               )
        self.integration_display.editingFinished.connect(partial(self.set_slider_value,
                                                                 display_box=self.integration_display,
                                                                 slider_widget=self.integration_time_slider
                                                                 )
                                                         )
        self.gain_max.editingFinished.connect(partial(self.slider_bounds_changed,
                                                      min_or_max="max",
                                                      setting='gain',
                                                      display_box=self.gain_max,
                                                      slider_widget=self.gain_slider
                                                      )
                                              )
        self.gain_min.editingFinished.connect(partial(self.slider_bounds_changed,
                                                      min_or_max="min",
                                                      setting='gain',
                                                      display_box=self.gain_min,
                                                      slider_widget=self.gain_slider
                                                      )
                                              )
        self.gain_slider.floatValueChanged.connect(partial(self.display_new_slider_value,
                                                           display_box=self.gain_display,
                                                           slider_widget=self.gain_slider
                                                           )
                                                   )
        self.gain_display.editingFinished.connect(partial(self.set_slider_value,
                                                          display_box=self.gain_display,
                                                          slider_widget=self.gain_slider
                                                          )
                                                  )
        self.offset_max.editingFinished.connect(partial(self.slider_bounds_changed,
                                                        min_or_max="max",
                                                        setting='offset',
                                                        display_box=self.offset_max,
                                                        slider_widget=self.offset_slider
                                                        )
                                                )
        self.offset_min.editingFinished.connect(partial(self.slider_bounds_changed,
                                                        min_or_max="min",
                                                        setting='offset',
                                                        display_box=self.offset_min,
                                                        slider_widget=self.offset_slider
                                                        )
                                                )
        self.offset_slider.floatValueChanged.connect(partial(self.display_new_slider_value,
                                                             display_box=self.offset_display,
                                                             slider_widget=self.offset_slider
                                                             )
                                                     )
        self.offset_display.editingFinished.connect(partial(self.set_slider_value,
                                                            display_box=self.offset_display,
                                                            slider_widget=self.offset_slider
                                                            )
                                                    )

        # Connect slider value changed to camera settings
        self.integration_time_slider.floatValueChanged.connect(partial(self.slider_value_changed,
                                                                       setting="integration"
                                                                       )
                                                               )
        self.gain_slider.floatValueChanged.connect(partial(self.slider_value_changed,
                                                           setting="gain"
                                                           )
                                                   )
        self.offset_slider.floatValueChanged.connect(partial(self.slider_value_changed,
                                                             setting="offset"
                                                             )
                                                     )

        self.advanced_settings_btn.clicked.connect(self.advanced_settings.show)

        # self.linescans.setEnabled(False)
        # self.histogram.setEnabled(False)
        # Hide all instruments to begin with.
        # self.hide_all_instr_settings()

    def displayed_instr_changed(self, instrument_text):
        if 'Attollo' in instrument_text:
            # self.histogram.setEnabled(True)
            self.attollo_settings_frame.setEnabled(True)
            # self.linescans.setEnabled(True)
            self.start_stop.start_feed_btn.setEnabled(True)
            self.initialize_selected_instrument.emit(self.instruments.currentData())

        elif instrument_text != '':
            self.start_stop.stop_feed_btn.setEnabled(True)
            # self.linescans.setEnabled(True)
            self.attollo_settings_frame.setEnabled(False)
            # self.histogram.setEnabled(False)

        else:
            pass
            # self.linescans.setEnabled(False)

    def slider_bounds_changed(self,
                              min_or_max: str,
                              setting: str,
                              display_box: QLineEdit,
                              slider_widget: common.FloatSlider
                              ):
        val = common.input2num(display_box.text())
        if min_or_max == "min":
            if val < self.absolute_slider_bounds[setting]["min"]:
                display_box.setText(self.previous_slider_bounds[setting]["min"])
            else:
                slider_widget.setRange(val, slider_widget.maximum())
                self.previous_slider_bounds[setting]["min"] = str(val)

        elif min_or_max == "max":
            if val > self.absolute_slider_bounds[setting]["max"]:
                display_box.setText(self.previous_slider_bounds[setting]["max"])
            else:
                slider_widget.setRange(slider_widget.minimum(), val)
                self.previous_slider_bounds[setting]["max"] = str(val)

    @staticmethod
    def display_new_slider_value(val, display_box: QLineEdit,
                                 slider_widget: common.FloatSlider
                                 ):
        if slider_widget.precision == 0:
            display_box.setText(str(int(val)))
        else:
            display_box.setText(str(round(val, slider_widget.precision)))

    @staticmethod
    def set_slider_value(display_box: QLineEdit,
                         slider_widget: common.FloatSlider
                         ):
        val = common.input2num(display_box.text())
        if val is None:
            val = int(slider_widget.value()) if slider_widget.precision == 0 else slider_widget.value()
            display_box.setText(str(val))
        else:
            if val <= slider_widget.minimum():
                val = int(slider_widget.minimum()) if slider_widget.precision == 0 else slider_widget.minimum()
                display_box.setText(str(val))
            elif val >= slider_widget.maximum():
                val = int(slider_widget.maximum()) if slider_widget.precision == 0 else slider_widget.maximum()
                display_box.setText(str(val))

            slider_widget.setValue(val)

    def slider_value_changed(self, value: float,
                             setting: Literal["integration", "gain", "offset"]
                             ):

        instr = self.instruments.currentData()["Instance"]
        match setting:
            case "integration":
                try:
                    instr.validate_integration_time(value)
                except (ValueError, TypeError):
                    log_s.warning(f"Attempted to set invalid integration time. Not changing. (Value: {value})")
                else:
                    instr.integration_time = value
                    new_value = instr.integration_time
                    self.display_new_slider_value(new_value,
                                                  self.integration_display,
                                                  self.integration_time_slider
                                                  )
                    # self.integration_display.setText(str(new_value))
            case "gain":
                try:
                    instr.validate_gain(value)
                except (ValueError, TypeError):
                    log_s.warning(f"Attempted to set invalid gain. Not changing. (Value: {value})")
                else:
                    instr.gain = value
                    new_value = instr.gain
                    self.display_new_slider_value(new_value,
                                                  self.gain_display,
                                                  self.gain_slider
                                                  )
            case "offset":
                value = int(value)
                try:
                    instr.validate_offset(value)
                except (ValueError, TypeError):
                    log_s.warning(f"Attempted to set invalid offset. Not changing. (Value: {value})")
                else:
                    instr.offset = value
                    new_value = instr.offset
                    self.display_new_slider_value(new_value,
                                                  self.offset_display,
                                                  self.offset_slider
                                                  )

    def changed_trigger_mode(self,
                             gui_state: Qt.CheckState
                             ):
        # TODO: Fix this
        instr = self.instruments.currentData()["Instance"]
        camera_state = instr.trigger_mode

        match camera_state, gui_state:
            case "continuous", Qt.Checked:
                instr.trigger_mode = "trigger"
            case "trigger", Qt.Unchecked:
                instr.trigger_mode = "continuous"
            case _, _:
                log_s.warning(f"GUI and camera trigger states out of sync. GUI: {gui_state}, Camera: {camera_state}."
                              f"\nKeeping camera state to attempting to sync with GUI."
                              f"\nIf problem persists, please restart the connection and report issue to Matthew"
                              f" @ mlarkins@freedomphotonics.com.")

    def changed_frame_rate(self):
        instr = self.instruments.currentData()["Instance"]
        new_frame_rate = self.frame_rate.text()
        try:
            new_frame_rate = int(round(float(new_frame_rate), 0))
        except ValueError:
            self.frame_rate.setText(str(instr.frame_rate))
        else:
            new_frame_rate = int(round(float(new_frame_rate), 0))
            try:
                instr.frame_rate = new_frame_rate
            except ValueError:
                log_s.warning(f"Invalid frame rate entered: {new_frame_rate}. Frame rate on camera not updated.")
                self.frame_rate.setText(str(instr.frame_rate))
            else:
                camera_frame_rate = instr.frame_rate
                try:
                    assert new_frame_rate == camera_frame_rate
                except AssertionError:
                    log_s.warning(f"Unknown error occurred. Frame rate on camera not updated. User entered "
                                  f"{new_frame_rate}, but camera reported {camera_frame_rate}.")

                self.frame_rate.setText(str(new_frame_rate))
                self.update_main_window_frame_rate.emit(new_frame_rate)


class RowLinescan(common.SubPlotViewer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         x_axis_length=VideoWorker.resolution[0],
                         plot_title="Row Linescan",
                         position_type='Pixels',
                         **kwargs)

        self.setLimits(xMin=0,
                       xMax=VideoWorker.resolution[0] + (VideoWorker.resolution[0] // 10),
                       yMin=0,
                       yMax=67000,
                       minXRange=VideoWorker.resolution[0],
                       minYRange=67000
                       )
        self.plot_area.getViewBox().setXRange(min=0,
                                              max=VideoWorker.resolution[0] + (VideoWorker.resolution[0] // 10),
                                              padding=0.2
                                              )
        self.plot_area.getViewBox().setYRange(min=0,
                                              max=MAX_INT_16,
                                              padding=0.2
                                              )

        self.getAxis('bottom').setTickSpacing(levels=[(VideoWorker.resolution[0]//4, 0),
                                                      (VideoWorker.resolution[0]//8, 0)
                                                      ]
                                              )

        self.getAxis('left').setTickSpacing(levels=[(MAX_INT_16//2, 0),
                                                    (MAX_INT_16//4, 0),
                                                    (MAX_INT_16//8, 0)]
                                            )

    def update_data(self,
                    linescan_data: np.ndarray[np.uint16],
                    ):
        assert linescan_data.shape == (VideoWorker.resolution[0],)

        # This should allow the plot to be updated without having to re-link the axes every time
        self.plot_area.setData(linescan_data[::-1])


class ColumnLinescan(common.SubPlotViewer):
    def __init__(self,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args,
                         x_axis_length=VideoWorker.resolution[1],
                         plot_title="Column Linescan",
                         position_type='Pixels',
                         **kwargs
                         )

        self.setLimits(xMin=0,
                       xMax=VideoWorker.resolution[1] + (VideoWorker.resolution[1] // 10),
                       yMin=0,
                       yMax=67000,
                       minXRange=VideoWorker.resolution[1],
                       minYRange=67000
                       )
        self.plot_area.getViewBox().setXRange(min=0,
                                              max=VideoWorker.resolution[1] + (VideoWorker.resolution[1] // 10),
                                              padding=0.2
                                              )
        self.plot_area.getViewBox().setYRange(min=0,
                                              max=MAX_INT_16,
                                              padding=0.2
                                              )

        self.getAxis('bottom').setTickSpacing(levels=[(VideoWorker.resolution[1]//4, 0),
                                                      (VideoWorker.resolution[1]//8, 0)
                                                      ]
                                              )
        self.getAxis('left').setTickSpacing(levels=[(MAX_INT_16//2, 0),
                                                    (MAX_INT_16//4, 0)
                                                    ]
                                            )

    def update_data(self,
                    linescan_data: np.ndarray[np.uint16],
                    ):
        assert linescan_data.shape == (VideoWorker.resolution[1],)

        # This should allow the plot to be updated without having to re-link the axes every time
        self.plot_area.setData(linescan_data)


class LinescanPlots:
    def __init__(self):
        self.row_linescan = RowLinescan()
        self.column_linescan = ColumnLinescan()

        self.row_thread = QThread()
        self.row_linescan.moveToThread(self.row_thread)
        self.row_thread.start()

        self.column_thread = QThread()
        self.column_linescan.moveToThread(self.column_thread)
        self.column_thread.start()

    def update_data(self, image_data: np.ndarray[np.uint16], central_lobe_xy: dict[str, int]):
        try:
            row_data = image_data[central_lobe_xy["y"], :]
            column_data = image_data[:, central_lobe_xy["x"]]
        except IndexError as error:
            log_s.error("An error occurred while trying to update row/column linescans."
                        f"\n\ncentral lobe coordinates: x={central_lobe_xy['x']} y={central_lobe_xy['y']}")
        else:
            self.row_linescan.update_data(row_data)
            self.column_linescan.update_data(column_data)

    def setVisible(self, visible: bool):
        self.row_linescan.setVisible(visible)
        self.column_linescan.setVisible(visible)


class HistogramPlot(pg.PlotWidget):
    def __init__(self,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args,
                         **kwargs
                         )

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.num_bins = 65536//512
        self.num_pixels = VideoWorker.resolution[0] * VideoWorker.resolution[1]
        self.plot_area = self.plot()

        plot_item = self.getPlotItem()
        plot_item.setTitle("Histogram")
        plot_item.setLabel('left', '# of Pixels')
        plot_item.setLabel('bottom', 'Pixel Intensity (a.u.)')

        self.setLimits(xMin=0, xMax=MAX_INT_16 - 1 + 6144, yMin=0, yMax=self.num_pixels, minXRange=10000,
                       minYRange=10)
        self.plot_area.getViewBox().setXRange(min=0, max=MAX_INT_16 - 1 + 6144, padding=0.2)
        self.plot_area.getViewBox().setYRange(min=0, max=self.num_pixels, padding=0.2)
        x_axis = self.getAxis('bottom')
        x_axis.setTickSpacing(levels=[(65536//4, 0), (65536//16, 0)])
        x_axis.showLabel()
        y_axis = self.getAxis('left')
        y_axis.setTickSpacing(levels=[(self.num_pixels//2, 0), (self.num_pixels//4, 0), (self.num_pixels//8, 0)])
        y_axis.showLabel()
        self.disableAutoRange(axis=pg.ViewBox.XYAxes)
        self.setAntialiasing(True)

    @pyqtSlot()
    def update_data(self, pixel_data: np.ndarray[np.uint16]):
        new_data = pixel_data.ravel()
        freq, bin_edges = np.histogram(new_data, bins=self.num_bins)

        # This should allow the plot to be updated without having to re-link the axes every time
        self.plot_area.setData(bin_edges, freq, fillLevel=0, stepMode="center", brush=(0, 0, 255, 150))


class SubPlotLayout(QVBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.linescan_plots = LinescanPlots()

        self.histogram_thread = QThread()
        self.histogram_plot = HistogramPlot()
        self.histogram_plot.moveToThread(self.histogram_thread)
        self.histogram_thread.start()

        self.linescan_plots.setVisible(True)
        self.histogram_plot.setVisible(True)

        self.addWidget(self.linescan_plots.row_linescan)
        self.addWidget(self.linescan_plots.column_linescan)
        self.addWidget(self.histogram_plot)


class VideoFeed(common.MainPlotViewer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = np.zeros((VideoWorker.resolution[0],
                              VideoWorker.resolution[1]
                              ),
                             dtype=np.uint16
                             )
        self.image = pg.ImageItem(self.data,
                                  autoLevels=False,
                                  )

        column_idx = VideoWorker.resolution[0] / 2
        row_idx = VideoWorker.resolution[1] / 2

        self.column_linescan_marker = pg.InfiniteLine(pos=column_idx, angle=90, pen='r')
        self.row_linescan_marker = pg.InfiniteLine(pos=row_idx, angle=0, pen='r')

        marker_color = QColor(Qt.darkYellow)
        marker_color.setAlphaF(0.5)
        marker_pen = QPen(marker_color)
        marker_pen.setStyle(Qt.PenStyle.DashLine)

        self.column_linescan_marker.setPen(marker_pen)
        self.row_linescan_marker.setPen(marker_pen)

        self.invertY(True)
        self.invertX(True)

        self.column_linescan_marker.setVisible(False)
        self.row_linescan_marker.setVisible(False)

        self.view_box = self.plotItem.getViewBox()

        self.pixel_peaker = pg.TargetItem(pos=(0, 0),
                                          symbol='o',
                                          size=5,
                                          movable=False,
                                          pen='r',
                                          brush='r',
                                          )
        self.pixel_peaker.setVisible(False)

        self.addItem(self.image)
        self.addItem(self.column_linescan_marker)
        self.addItem(self.row_linescan_marker)
        self.addItem(self.pixel_peaker)

        self.plotItem.scene().sigMouseMoved.connect(self.mouse_moved)

    def update_data(self, image_data: np.ndarray[np.uint16], central_lobe_xy: dict[str, int]):
        self.data = image_data
        self.image.setImage(self.data,
                            axisOrder='row-major',
                            autoLevels=False
                            )

        self.column_linescan_marker.setPos(central_lobe_xy["x"])
        self.row_linescan_marker.setPos(central_lobe_xy["y"])

    def are_linescan_markers_visible(self) -> bool:
        if self.column_linescan_marker.isVisible() and self.row_linescan_marker.isVisible():
            return True
        else:
            return False

    def set_linescan_markers_visible(self, true_false: bool):
        self.column_linescan_marker.setVisible(true_false)
        self.row_linescan_marker.setVisible(true_false)

    def mouse_moved(self, pos: QPointF):
        if not self.plotItem.sceneBoundingRect().contains(pos):
            if self.pixel_peaker.isVisible():
                self.pixel_peaker.setVisible(False)
        else:
            mouse_point = self.view_box.mapSceneToView(pos)
            x_idx = round(mouse_point.x())
            y_idx = round(mouse_point.y())
            x_lim, y_lim = self.data.shape
            if 0 < x_idx < x_lim and 0 < y_idx < y_lim:
                if not self.pixel_peaker.isVisible():
                    self.pixel_peaker.setVisible(True)
                self.pixel_peaker.setPos(x_idx, y_idx)
                value = self.data[x_idx, y_idx]
                self.pixel_peaker.setLabel(str(value),
                                           labelOpts={'color': 'r',
                                                      'offset': (-5, -10),
                                                      'ensureInBounds': True
                                                      }
                                           )
            else:
                if self.pixel_peaker.isVisible():
                    self.pixel_peaker.setVisible(False)


class AllCameraPlotsLayout(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.subplots = SubPlotLayout()

        self.video_feed_worker = VideoWorker()
        self.video_feed = VideoFeed(resolution=VideoWorker.resolution)
        self.video_feed.moveToThread(self.video_feed_worker)
        self.video_feed_worker.start()

        self.video_feed.setMinimumSize(*VideoWorker.resolution)
        self.video_feed.resize(*VideoWorker.resolution)

        self.addSpacing(20)
        self.addWidget(self.video_feed, stretch=2)
        self.addSpacing(10)
        self.addLayout(self.subplots, stretch=1)
        self.addSpacing(20)


class VideoWorker(QThread):
    data_ready_to_display_signal = pyqtSignal(np.ndarray, dict)

    resolution = [640, 512]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blob_detector = self.blob_detector()
        self.blob_warning_counter = 0
        self.last_known_blob_centroid = {"x": int((self.resolution[0] - 1) // 2),
                                         "y": int((self.resolution[1] - 1) // 2)
                                         }

        # Gets updated by ProgramsMenu in startup.py
        self.test_info = None

        # Gets updated by initialize_instr_and_gui
        self.instr = None
        self.is_live = False
        self.data_to_send = []


    @staticmethod
    def blob_detector():
        # noinspection PyUnresolvedReferences
        _params = cv2.SimpleBlobDetector_Params()

        # The blob detector converts the image into a series of binary images at different threshold levels, in
        # intervals of _params.thresholdStep. To quote a reddit thread I found on the subject - "The lower minimum
        # threshold will pick up more objects and the higher [maximum?] will pick out unique objects from an
        # otherwise seemingly blob".
        _params.minThreshold = 90
        _params.maxThreshold = 200

        _params.filterByColor = True
        _params.blobColor = 255  # Not sure if this is only going to select purely white blobs or "lighter" ones

        _params.filterByArea = True
        _params.minArea = 30
        _params.maxArea = 10000

        _params.filterByCircularity = True
        _params.minCircularity = 0.1
        _params.maxCircularity = 1

        _params.filterByInertia = True
        _params.minInertiaRatio = 0.2
        _params.maxInertiaRatio = 1

        # noinspection PyUnresolvedReferences
        return cv2.SimpleBlobDetector_create(_params)

    @pyqtSlot(np.ndarray)
    def update_video_frame_slot(self,
                                pixel_data: np.ndarray[np.uint16]
                                ):
        def find_central_lobe() -> dict[str, int]:
            # Uniformly downscale the image to uint8 for compatibility with opencv SimpleBlobDetector
            keypoints = self.blob_detector.detect((pixel_data / 257).astype(np.uint8))
            match len(keypoints):
                case 0:
                    x = self.last_known_blob_centroid["x"]
                    y = self.last_known_blob_centroid["y"]
                    return {"x": round(x), "y": round(y)}
                case 1:
                    x, y = keypoints[0].pt
                    self.last_known_blob_centroid["x"] = x
                    self.last_known_blob_centroid["y"] = y
                    return {"x": round(x), "y": round(y)}
                case _:
                    self.blob_warning_counter += 1

                    if self.blob_warning_counter % 120 == 0:
                        warnings.warn('Too many blobs found. Either detection parameters need to be tuned, or a '
                                      'new central lobe centroid detection method must be implemented')

                    x = self.last_known_blob_centroid["x"]
                    y = self.last_known_blob_centroid["y"]
                    return {"x": x, "y": y}

        def send_to_driver_if_requested():
            if self.is_live and self.instr.data_manager is not None:
                if (rem_frames := self.instr.data_manager.read_remaining_frame_count()) > 0:
                    if self.instr.data_manager.get_test_info_widget() is None:
                        self.instr.data_manager.set_test_info_widget(self.test_info)

                    len_before = len(self.instr.data_manager.data)
                    self.instr.data_manager.data.append(pixel_data)
                    assert len(self.instr.data_manager.data) > len_before

                    self.instr.data_manager.write_remaining_frame_count(rem_frames - 1)
                    if self.instr.data_manager.read_remaining_frame_count() == 0:
                        self.instr.data_manager.data_compiled.emit()

        if pixel_data is None:
            pixel_data = np.random.rand(self.resolution[1], self.resolution[0]) * MAX_INT_16 - 1
            pixel_data = pixel_data.astype(np.uint16)

        send_to_driver_if_requested()

        central_lobe_xy = find_central_lobe()

        self.data_ready_to_display_signal.emit(pixel_data, central_lobe_xy)


class BeamImagingMainWindow(QMainWindow):
    """Main window for beam image monitoring while performing beam waist imaging.
    """
    closing = pyqtSignal()
    request_video_frame_signal = pyqtSignal(dict)

    def __init__(self, instr_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --------------------------------------
        self.instr_handler = instr_handler
        self.available_instr = None

        self.stop_updating = False
        self.is_live = False
        self.instr = None
        self.frame_rate = 0

        # --------------------------------------
        # Boilerplate stuff.
        self.setWindowTitle('Beam Imaging Monitor')
        self.resize(1200,
                    700
                    )
        # Central widget.
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Main layout.
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.central_widget.setLayout(self.layout)

        # --------------------------------------------------------------------
        # User interaction.
        self.info = MonitorSetupInfo()
        self.plot_layouts = AllCameraPlotsLayout()
        self.data_collection = DataCollection()

        self.video_feed = self.plot_layouts.video_feed
        self.video_feed_worker = self.plot_layouts.video_feed_worker
        self.subplots = self.plot_layouts.subplots

        self.layout.addWidget(self.info)
        self.layout.addSpacing(8)
        self.layout.addLayout(self.data_collection)
        self.layout.addSpacing(8)
        self.layout.addLayout(self.plot_layouts, stretch=1)
        self.layout.addSpacing(10)

        # --------------------------------------
        # Connect signals and slots to buttons.
        self.info.start_stop.start_feed_btn.released.connect(self.start_video_frame_slot)
        self.info.start_stop.stop_feed_btn.released.connect(self.stop_video_frame_slot)

        self.info.initialize_selected_instrument[dict].connect(self.initialize_instr_and_gui)
        self.info.advanced_settings.reinitialize_instrument[common.EmptyObject].connect(self.initialize_instr_and_gui)

        self.info.update_main_window_frame_rate.connect(self.frame_rate_changed)

        self.request_video_frame_signal.connect(self.instr_handler.get_video_frame_slot)
        self.instr_handler.video_frame_data_ready_signal.connect(self.video_feed_worker.update_video_frame_slot)

        self.video_feed_worker.data_ready_to_display_signal.connect(self.update_video_display)

        self.data_collection.save_beam_image_signal.connect(self.save_beam_image)
        self.data_collection.save_background_image_signal.connect(self.save_background_image)

    @pyqtSlot(dict)
    def save_beam_image(self, test_info):
        if self.instr is not None and self.is_live:
            self.instr.save_beam_image_data(test_info)
            self.data_collection.save_beam_img_btn.setEnabled(False)
            while self.instr.data_manager.isRunning():
                continue
            else:
                self.data_collection.save_beam_img_btn.setEnabled(True)

    @pyqtSlot(dict)
    def save_background_image(self, test_info):
        if self.instr is not None and self.is_live:
            self.instr.save_background_image_data(test_info)
            self.data_collection.save_bg_img_btn.setEnabled(False)
            while self.instr.data_manager.isRunning():
                continue
            else:
                self.data_collection.save_bg_img_btn.setEnabled(True)

    @pyqtSlot()
    def request_video_frame(self):
        instrument = self.info.instruments.currentData()

        if self.stop_updating:
            self.stop_updating = False
            self.enable_interface(True)
            return
        else:
            self.enable_interface(False)

        if not instrument['Connected']:
            log_s.error(f'Cannot start video feed. Instrument{instrument["Unique_id"]} is not connected.')
            return

        else:
            self.request_video_frame_signal.emit(instrument)

    def enable_interface(self, true_false):
        # If True, enable these.
        self.info.start_stop.start_feed_btn.setEnabled(true_false)
        self.info.instruments.setEnabled(true_false)

        # If True, disable these.
        self.info.start_stop.stop_feed_btn.setEnabled(not true_false)
        if not self.video_feed.are_linescan_markers_visible():
            self.video_feed.set_linescan_markers_visible(True)

    @pyqtSlot(dict)
    @pyqtSlot(common.EmptyObject)
    def initialize_instr_and_gui(self, instr_info: dict | common.EmptyObject):
        if isinstance(instr_info, common.EmptyObject):
            instr_info = self.info.instruments.currentData()

        if instr_info["Connected"]:
            instr = instr_info["Instance"]
            self.video_feed_worker.instr = instr_info["Instance"]
            self.instr = instr

            # Turn off AEC & AGC
            instr.auto_exposure_control = 'disabled'
            instr.auto_gain_control = "manual"

            self.info._current_frame_rate = instr.frame_rate

            self.frame_rate = self.info._current_frame_rate

            self.info._current_integration_time = round(instr.integration_time, 2)
            self.info._current_gain = round(instr.gain, 2)
            self.info._current_offset = round(instr.offset, 0)
            trigger_mode = instr.trigger_mode

            if trigger_mode == 'trigger':
                self.info.trigger_toggle.setChecked(True)
            else:
                self.info.trigger_toggle.setChecked(False)

            if ((is_min := self.info._current_integration_time < float(self.info.integration_min.text())) or
                           self.info._current_integration_time > float(self.info.integration_max.text())):
                if is_min:
                    self.info.integration_min.setText(str(self.info._current_integration_time))
                    self.info.integration_time_slider.setMinimum(self.info._current_integration_time)
                else:
                    self.info.integration_max.setText(str(self.info._current_integration_time))
                    self.info.integration_time_slider.setMaximum(self.info._current_integration_time)

            if ((is_min := self.info._current_gain < float(self.info.gain_min.text())) or
                           self.info._current_gain > float(self.info.gain_max.text())):
                if is_min:
                    self.info.gain_min.setText(str(self.info._current_gain))
                    self.info.gain_slider.setMinimum(self.info._current_gain)
                else:
                    self.info.gain_max.setText(str(self.info._current_gain))
                    self.info.gain_slider.setMaximum(self.info._current_gain)

            if ((is_min := self.info._current_offset < float(self.info.offset_min.text())) or
                           self.info._current_offset > float(self.info.offset_max.text())):
                if is_min:
                    self.info.offset_min.setText(str(self.info._current_offset))
                    self.info.offset_slider.setMinimum(self.info._current_offset)
                else:
                    self.info.offset_max.setText(str(self.info._current_offset))
                    self.info.offset_slider.setMaximum(self.info._current_offset)

            self.info.frame_rate.setText(str(self.info._current_frame_rate))
            self.info.integration_display.setText(str(self.info._current_integration_time))
            self.info.gain_display.setText(str(self.info._current_gain))
            self.info.offset_display.setText(str(self.info._current_offset))

            self.info.integration_time_slider.setValue(self.info._current_integration_time)
            self.info.gain_slider.setValue(self.info._current_gain)
            self.info.offset_slider.setValue(self.info._current_offset)

            self.info.absolute_slider_bounds['integration'] = instr.integration_time_bounds
            self.info.absolute_slider_bounds['gain'] = instr.gain_bounds
            self.info.absolute_slider_bounds['offset'] = instr.offset_bounds

            # Initialize advanced settings
            self.info.advanced_settings.instr = instr
            self.info.advanced_settings.reinitializing = True
            self.info.advanced_settings.NUC_modes.clear()
            self.info.advanced_settings.AEC_modes.clear()
            self.info.advanced_settings.AGC_modes.clear()

            self.info.advanced_settings.NUC_modes.addItems([key.upper() for key in instr.NUC_modes.keys()])
            self.info.advanced_settings.AEC_modes.addItems([key.upper() for key in instr.AEC_modes.keys()])
            self.info.advanced_settings.AGC_modes.addItems([key.upper() for key in instr.AGC_modes.keys()])
            self.info.advanced_settings.reinitializing = False

            self.info.advanced_settings.NUC_modes.setCurrentText(instr.non_uniformity_correction.upper())
            self.info.advanced_settings.AEC_modes.setCurrentText(instr.auto_exposure_control.upper())
            self.info.advanced_settings.AGC_modes.setCurrentText(instr.auto_gain_control.upper())

    @pyqtSlot(dict)
    def update_instr_list_slot(self, instr):
        self.info.instruments.clear()
        self.available_instr = {}
        for unique_id, instr in instr.items():
            if 'Camera' in instr['Type']:
                self.available_instr[unique_id] = self.instr_handler.available_instr[unique_id]
                self.info.instruments.addItem(unique_id, self.instr_handler.available_instr[unique_id])

    @pyqtSlot()
    def start_video_frame_slot(self):
        if self.available_instr[self.info.instruments.currentText()]['Connected']:
            self.is_live, self.video_feed_worker.is_live = True, True
            self.request_video_frame()

    @pyqtSlot()
    def stop_video_frame_slot(self):
        self.is_live, self.video_feed_worker.is_live = False, False
        self.stop_updating = True

    def frame_rate_changed(self, new_frame_rate: int):
        self.frame_rate = new_frame_rate

    @pyqtSlot(np.ndarray, dict)
    def update_video_display(self, pixel_data: np.ndarray[np.uint16], central_lobe_xy: dict[str, int]):
        self.video_feed.update_data(pixel_data,
                                    central_lobe_xy
                                    )
        self.subplots.linescan_plots.update_data(pixel_data,
                                                 central_lobe_xy
                                                 )
        self.subplots.histogram_plot.update_data(pixel_data)

        QTimer.singleShot(int((1 / self.frame_rate) * 1e3), self.request_video_frame)
