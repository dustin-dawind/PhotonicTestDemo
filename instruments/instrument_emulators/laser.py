import numpy as np

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)


class LaserEmulator(QObject):
    power_value_ready = pyqtSignal(float)
    voltage_value_ready = pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # -------------- Characteristic parameters --------------
        self._v_th = 0.025852  # This is constant
        self._non_ideal_factor = 0
        self.exp_denom = self._v_th * self._non_ideal_factor

        self._threshold = 0
        self._ase_multiplier = 0
        self._slope_eff = 0
        self.i_rev_sat = 0
        # --------------------------------------------------------

        self.swap_device()  # Initialize characteristic parameters

        self._i_current = 0
        self._psu_on = False

    def _f_liv(self, current):
        def ase_func(x):
            return np.exp(x * self._ase_multiplier) - 1

        def lasing_func(x):
            return self._slope_eff * (x - self._threshold) + ase_func(self._threshold)

        if self._psu_on:
            if 0 <= current <= self._threshold:
                return ase_func(current)
            elif current > self._threshold:
                return lasing_func(current)
            else:
                return 0
        else:
            return 0

    def _f_v_from_i(self, input_current):
        if self._psu_on:
            if input_current > 0:
                return self.exp_denom * np.log((1 / self.i_rev_sat) * input_current + 1)  # Inverse Shockley diode equation
            else:
                return 0
        else:
            return 0

    @pyqtSlot(float)
    def update_power(self, input_current):
        self._i_current = input_current
        power = self._f_liv(self._i_current)
        self.power_value_ready.emit(power)
        return power

    @pyqtSlot()
    def update_voltage(self):
        voltage = self._f_v_from_i(self._i_current)
        self.voltage_value_ready.emit(voltage)
        return voltage

    @pyqtSlot(str)
    def psu_status_changed(self, status: bool):
        match status:
            case "ON":
                self._psu_on = True
            case "OFF":
                self._psu_on = False

    def swap_device(self):
        # LIV parameters
        self._threshold = np.random.normal(100, 10)
        self._ase_multiplier = 1 / np.random.normal(70, 5)
        self._slope_eff = np.random.normal(0.9, 0.025)

        # RevIV parameters
        self._non_ideal_factor = 1.2 + np.random.normal(0, 0.025)
        self.exp_denom = self._v_th * self._non_ideal_factor

        self.i_rev_sat = 1e-14 / np.random.normal(50, 10)

