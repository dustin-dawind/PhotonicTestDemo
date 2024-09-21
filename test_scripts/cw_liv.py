from typing import NewType

from testing import TestClass

# Can only use these for type hinting => need instruments to be the original instance in order to synchronize everything
from instruments import (
    psu,
    power_meter
)


PSUType = NewType('PSUType', psu.Instrument)
PowerMeterType = NewType('PowerMeterType', power_meter.Instrument)

PossibleInstruments = PSUType | PowerMeterType


class Test(TestClass):
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

    def start_test(self):
        self.psu.reset()
        self.power_meter.reset()

        self.set_axes_titles_signal.emit('Current (mA)', 'Power (mW)', 'Efficiency (%)')

        self.psu.output = 'ON'

        for device_num in range(1,
                                self.num_devices + 1
                                ):
            self.new_device(device_num)
            for setpoint in range(1, 1201, 50):
                self.start_timer()
                self.psu.i_setpoint = setpoint

                i_set = self.psu.i_setpoint
                i_actual = self.psu.measure_current()  # in mA
                v_actual = self.psu.measure_voltage()  # in V
                power = self.power_meter.measure()  # in mW

                eff = (i_actual * v_actual * 1e3) / (power * 1e3)

                self.send_for_plotting(device_num,
                                       i_actual,
                                       power,
                                       eff
                                       )
                self.record_time_elapsed(device_num)

        self.psu.output = 'OFF'
        self.print_analytics()



