from PyQt6.QtCore import (
    pyqtSignal,
    pyqtSlot,
    Qt
)
from PyQt6.QtWidgets import (
    QSlider
)


class FloatSlider(QSlider):
    slider_value_changed_signal = pyqtSignal(float)
    def __init__(self, precision=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._multiplier = 10 ** precision
        self.setOrientation(Qt.Horizontal)

        self.valueChanged.connect(self.slider_value_changed)

    @pyqtSlot(int)
    def slider_value_changed(self):
        value = float(super().value()) / self._multiplier
        self.slider_value_changed_signal.emit(value)

    def value(self) -> float:
        return float(super().value()) / self._multiplier

    def setValue(self, value: float):
        super().setValue(int(value * self._multiplier))

    def minimum(self) -> float:
        return float(super().minimum()) / self._multiplier

    def setMinimum(self, value: float):
        super().setMinimum(int(value * self._multiplier))

    def maximum(self) -> float:
        return float(super().maximum()) / self._multiplier

    def setMaximum(self, value: float):
        super().setMaximum(int(value * self._multiplier))


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = FloatSlider()
    window.show()

    sys.exit(app.exec_())
