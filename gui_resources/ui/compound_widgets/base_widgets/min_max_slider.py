from gui_resources.ui.compound_widgets import utils
from gui_resources.ui.compound_widgets.base_widgets.float_slider import FloatSlider
from rich import print
from PyQt6.QtWidgets import (
    QLineEdit,
    QLabel
)
from PyQt6.QtCore import (
    pyqtSlot,
    QObject,
    Qt
)


class MinMaxSliderSetup(QObject):
    def __init__(self,
                 label,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)

        self.label = QLabel(label)
        self.label.setAlignment(Qt.AlignRight)

        self.min_display = QLineEdit()
        self.min_display.setAlignment(Qt.AlignCenter)

        self.max_display = QLineEdit()
        self.max_display.setAlignment(Qt.AlignCenter)

        self.position_display = QLineEdit()
        self.position_display.setAlignment(Qt.AlignCenter)

        self.slider = FloatSlider()

class MinMaxSliderObject(MinMaxSliderSetup):
    def __init__(self,
                 label="",
                 min_value: float = 0,
                 max_value: float = 10,
                 starting_position: float | None = None,
                 parent=None,
                 *args,
                 **kwargs
                 ):
        super().__init__(label, *args, **kwargs)

        self._min = min_value
        self._max = max_value

        if isinstance(starting_position, float) and min_value <= starting_position <= max_value:
            self._position = starting_position
        elif starting_position is None:
            self._position = self._min
        else:
            print(f"[red]ValueError: Slider position must within the minimum and maximum values "
                  f"({self._min}, {self._max}). Setting to minimum: {self._min}[/] ")
            self._position = self._min

        self.slider.setParent(parent)
        self.min_display.setParent(parent)
        self.max_display.setParent(parent)
        self.position_display.setParent(parent)
        self.label.setParent(parent)

        self.min_display.setText(str(self._min))
        self.max_display.setText(str(self._max))
        self.position_display.setText(str(self._position))

        self.slider.setMinimum(self._min)
        self.slider.setMaximum(self._max)
        self.slider.setValue(self._position)

        self.min_display.editingFinished.connect(self.set_min)
        self.max_display.editingFinished.connect(self.set_max)
        self.position_display.editingFinished.connect(self.set_position)
        self.slider.slider_value_changed_signal.connect(self.display_position)

    @pyqtSlot()
    def set_min(self):
        value = self.min_display.text()
        try:
            value = float(value)
        except ValueError:
            print(f"[red]ValueError: Slider minimum must be a number: {value}[/]")
            self.min_display.setText(str(self._min))
        else:
            self._min = value
            self.min_display.setText(str(value))
            self.slider.setMinimum(value)

    @pyqtSlot()
    def set_max(self):
        value = self.max_display.text()
        try:
            value = float(value)
        except ValueError:
            print(f"[red]ValueError: Slider maximum must be a number: {value}[/]")
            self.max_display.setText(str(self._max))
        else:
            self._max = value
            self.max_display.setText(str(value))
            self.slider.setMaximum(value)

    @pyqtSlot(float)
    def display_position(self, value: float):
        self.position_display.setText(str(value))

    @pyqtSlot()
    def set_position(self):
        value = self.position_display.text()
        try:
            value = float(value)
        except ValueError:
            print(f"[red]ValueError: Slider current must be a number: {value}[/]")
            self.position_display.setText(str(self._position))
        else:
            self._position = value
            self.position_display.setText(str(value))
            self.slider.setValue(value)

    def fix_line_edit_width(self, length=10):
        for widget in [self.min_display, self.max_display, self.position_display]:
            utils.fix_line_edit_width(widget, length=length)

