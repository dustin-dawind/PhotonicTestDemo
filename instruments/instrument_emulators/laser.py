import numpy as np
import pandas as pd
from dataclasses import dataclass

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)


@dataclass
class CharacteristicParameters:
    v_th: float = 0.025852
    non_ideal_factor: float = 1.2
    exp_denom: float = v_th * non_ideal_factor
    threshold: float = 100
    ase_multiplier: float = 70
    slope_eff: float = 0.7
    i_rev_sat: float = 10

    def randomize(self):
        self.threshold = np.random.uniform(80, 120)
        self.ase_multiplier = np.random.uniform(60, 80)
        self.slope_eff = np.random.uniform(0.6, 0.8)
        self.i_rev_sat = np.random.uniform(8, 20)


class LaserEmulator(QObject):
    power_value_ready = pyqtSignal(float)
    voltage_value_ready = pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # -------------- Characteristic parameters --------------
        self._base_parameters = CharacteristicParameters()
        self._non_ideal_factor = self._base_parameters.non_ideal_factor
        self.exp_denom = self._base_parameters.exp_denom

        self._threshold = self._base_parameters.threshold
        self._ase_multiplier = self._base_parameters.ase_multiplier
        self._slope_eff = self._base_parameters.slope_eff
        self.i_rev_sat = self._base_parameters.i_rev_sat
        # --------------------------------------------------------

        self._i_current = 0
        self._psu_on = False

        self._previous_device = pd.Series(index=["Wafer ID", "Field ID", "Device ID"])

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

    @pyqtSlot(pd.Series)
    def swap_device(self, new_device: pd.Series | None = None):
        if self._previous_device["Wafer ID"] == np.nan:
            pass
        elif new_device["Wafer ID"] != self._previous_device["Wafer ID"] or new_device["Field ID"] != self._previous_device["Field ID"]:
            self._base_parameters.randomize()

        # LIV parameters
        self._threshold = np.random.normal(self._base_parameters.threshold, 10)
        self._ase_multiplier = 1 / np.random.normal(self._base_parameters.ase_multiplier, 5)
        self._slope_eff = np.random.normal(self._base_parameters.slope_eff, 0.025)

        # RevIV parameters
        self._non_ideal_factor = np.random.normal(self._base_parameters.non_ideal_factor, 0.025)
        self.exp_denom = self._base_parameters.v_th * self._non_ideal_factor

        self.i_rev_sat = 1e-14 / np.random.normal(self._base_parameters.i_rev_sat, 1)
