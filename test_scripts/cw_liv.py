from typing import NewType

from testing import TestClass
# Can only use these for type hinting => need instruments to be the original instance in order to synchronize everything
from instruments import (
    psu,
    power_meter
)

from PyQt5.QtWidgets import QApplication

PSUType = NewType('PSUType', psu.Instrument)
PowerMeterType = NewType('PowerMeterType', power_meter.Instrument)

PossibleInstruments = PSUType | PowerMeterType


class Test(TestClass):
    def __init__(self,
                 instruments: dict[str, PossibleInstruments]
                 ):
        super().__init__()

        self.needed_instruments = ('power_meter', 'psu')

        for instrument in self.needed_instruments:
            if instrument == 'power_meter':
                self.power_meter = instruments.get(instrument, None)
            elif instrument == 'psu':
                self.psu = instruments.get(instrument, None)

        if self.psu is None or self.power_meter is None:
            raise ValueError(f'PSU and Power Meter must be specified. Got: {instruments}')

        self.num_devices = 5

    def start_test(self):
        # self.test_started_signal.emit(self.needed_instruments)
        self.psu.reset()
        self.power_meter.reset()

        self.set_plot_axes_titles('Current', 'Power', 'Efficiency')

        self.psu.output = 'ON'

        for device_num in range(1,
                                self.num_devices + 1
                                ):
            self.new_device(device_num)
            for setpoint in range(0, 1201, 50):
                self.process_events()
                if self.user_requested_stop:
                    self.psu.output = 'OFF'
                    self.test_finished()
                    return

                self.start_timer()
                self.psu.i_setpoint = setpoint

                i_set = self.psu.i_setpoint
                i_actual = self.psu.measure_current()  # in mA
                v_actual = self.psu.measure_voltage()  # in V
                power = self.power_meter.measure()  # in mW

                eff = 0
                if (e_power := i_actual * v_actual) != 0:
                    eff = power / e_power
                if eff > 1 or eff < 0 or setpoint < 150:
                    eff = 0

                self.send_for_plotting(device_num,
                                       i_actual,
                                       power,
                                       eff
                                       )
                self.record_time_elapsed(device_num)

        self.psu.output = 'OFF'
        self.print_analytics()
        self.test_finished()

