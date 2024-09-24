from typing import NewType
import pandas as pd
from test_class import TestClass
from collections import defaultdict

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
                 instruments: dict[str, PossibleInstruments],
                 device_definitions: pd.DataFrame
                 ):
        super().__init__()

        self.needed_instruments = ('power_meter', 'psu')


        self.devices = device_definitions

        for instrument in self.needed_instruments:
            if instrument == 'power_meter':
                self.power_meter = instruments.get(instrument, None)
            elif instrument == 'psu':
                self.psu = instruments.get(instrument, None)

        if self.psu is None or self.power_meter is None:
            raise ValueError(f'PSU and Power Meter must be specified. Got: {instruments}')

        self.num_devices = 5

        self.data = defaultdict(list)

    def start_test(self):
        self.psu.reset()
        self.power_meter.reset()

        self.set_plot_axes_titles('Current', 'Power', 'Efficiency')

        self.psu.output = 'ON'

        self.update_status("...")
        current_device = None
        for index, row in self.devices.iterrows():
            # if row["Device ID"] != current_device:
            #     self.new_device(current_device := (row["Field ID"] * 1e3 + row["Device ID"]))
            if index == 5:
                break

            for setpoint in range(0, 1201, 50):
                self.process_events()
                if self.user_requested_stop:
                    self.psu.output = 'OFF'
                    self.update_status("Stopped!")
                    self.test_finished()
                    return

                # self.start_timer()
                self.psu.i_setpoint = setpoint

                i_set = self.psu.i_setpoint
                i_actual = self.psu.measure_current()
                v_actual = self.psu.measure_voltage()
                power = self.power_meter.measure()

                eff = 0
                if (e_power := i_actual * v_actual) != 0:
                    eff = power / e_power
                if eff > 1 or eff < 0 or setpoint < 150:
                    eff = 0

                # self.send_for_plotting(current_device,
                #                        i_actual,
                #                        power,
                #                        eff
                #                        )

                self.data["Wafer ID"].append(row["Wafer ID"])
                self.data["Field ID"].append(row["Field ID"])
                self.data["Device ID"].append(row["Device ID"])
                self.data["Set Current (mA)"].append(i_set)
                self.data["Measured Current (mA)"].append(i_actual)
                self.data["Measured Voltage (V)"].append(v_actual)
                self.data["Measured Power (mW)"].append(power)
                self.data["Efficiency"].append(eff)

        self.psu.output = 'OFF'
        # self.print_analytics()
        self.save_data(self.data)
        self.update_status("Done!")
        self.test_finished()

