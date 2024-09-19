from typing import NewType

from instruments import psu, power_meter

from PyQt5.QtCore import (
    QObject,
    pyqtSignal
)


PSUType = NewType('PSUType', psu.Instrument)
PowerMeterType = NewType('PowerMeterType', power_meter.Instrument)

PossibleInstruments = PSUType | PowerMeterType


class Test(QObject):
    update_monitor = pyqtSignal(int, float, float, float)
    def __init__(self,
                 num_devices: int = 15,
                 parent=None,
                 **instruments: PossibleInstruments
                 ):
        super().__init__(parent=parent)

        self.num_devices = num_devices


        for instrument in instruments:
            if instrument == 'power_meter':
                self.power_meter = instruments[instrument]
            elif instrument == 'psu':
                self.psu = instruments[instrument]
            else:
                raise ValueError(f'Instrument {instrument} not supported by this test')

        if not (hasattr(self, 'power_meter') and hasattr(self, 'psu')):
            raise ValueError(f'A power meter and PSU are required to run {__file__}')

        self.psu.reset()
        self.power_meter.reset()

    def run(self):
        self.psu.output = 'ON'
        for device in range(self.num_devices):

            for setpoint in range(1201):
                self.psu.i_setpoint = setpoint

                power = self.power_meter.measure()
                i_set = self.psu.i_setpoint
                i_actual = self.psu.measure_current()
                v_actual = self.psu.measure_voltage()

                self.update_monitor.emit(device, i_actual, power, v_actual)








