import pandas as pd

from test_class import (
    TestClass,
    standard_test
)

# Can only use these for type hinting => need instruments to be the original instance in order to synchronize everything
from instruments import (
    PSU,
    PowerMeter
)


class Test(TestClass):
    def __init__(self,
                 # instruments: dict[str, PossibleInstruments],
                 device_definitions: pd.DataFrame
                 ):
        super().__init__()

        # The test_data_monitor will handle creating instance attributes for these instruments.
        # They may be referenced as `self.power_meter` and `self.psu` within `self.start_test()`
        self.needed_instruments = ('power_meter', 'psu')
        self.DUTs = device_definitions
        self.power_meter: PowerMeter | None = None
        self.psu: PSU | None = None

    @standard_test
    def run_test(self):
        self.set_plot_axes_titles('Current',
                                  'Power',
                                  'Efficiency'
                                  )

        self.psu.output = 'ON'

        test_setpoints = list(range(0, 1201, 50))
        self.send_total_num_data_points(len(test_setpoints) * len(self.DUTs.index))
        for index, row in self.DUTs.iterrows():
            self.new_device(row)

            for setpoint in test_setpoints:
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

                # This breaks if there is ever more than 256 devices to test, as the colormap only has 256 colors.
                # Can be fixed by reducing each device set to its mean plot after when a new device set is started
                # (i.e. when the wafer or field ID changes)

                self.send_for_plotting(row,
                                       i_actual,
                                       power,
                                       eff
                                       )

                self.data["Wafer ID"].append(row["Wafer ID"])
                self.data["Field ID"].append(row["Field ID"])
                self.data["Device ID"].append(row["Device ID"])
                self.data["Set Current (mA)"].append(i_set)
                self.data["Measured Current (mA)"].append(i_actual)
                self.data["Measured Voltage (V)"].append(v_actual)
                self.data["Measured Power (mW)"].append(power)
                self.data["Efficiency"].append(eff)

                self.update_test_progress()
                if self.user_requested_stop:
                    self.psu.output = 'OFF'
                    self.test_finished()
                    return


