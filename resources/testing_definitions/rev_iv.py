import numpy as np
import pandas as pd

from test_class import (
    TestClass,
    standard_test
)

# Can only use these for type hinting => need instruments to be the original instance in order to synchronize everything
from instruments import (
    PSU
)

class Test(TestClass):
    def __init__(self,
                 device_definitions: pd.DataFrame
                 ):
        super().__init__("Reverse_IV")

        # The test_data_monitor will handle creating instance attributes for these instruments.
        # They may be referenced as `self.power_meter` and `self.psu` within `self.start_test()`
        self.needed_instruments: tuple = ('psu',)  # Must be a tuple
        self.psu: PSU | None = None
        self.DUTs = device_definitions

    @standard_test
    def run_test(self):
        self.set_plot_axes_titles('Voltage',
                                  'Current'
                                  )

        self.psu.i_lim = 100e-3  # 1uA
        self.psu.output = 'ON'

        test_setpoints = list(np.linspace(-2., -0.5, 10)) + list(np.linspace(-0.5, 1.5, 40)) + list(np.linspace(1.5, 2., 5))
        self.send_total_num_data_points(len(test_setpoints) * len(self.DUTs.index))
        for index, row in self.DUTs.iterrows():
            self.new_device(row)

            for setpoint in test_setpoints:
                self.psu.v_setpoint = setpoint

                v_set = self.psu.v_setpoint
                v_actual = self.psu.measure_voltage()
                i_actual = self.psu.measure_current()

                # This breaks if there is ever more than 256 devices to test, as the colormap only has 256 colors.
                # Can be fixed by reducing each device set to its mean plot after when a new device set is started
                # (i.e. when the wafer or field ID changes)
                self.send_for_plotting(row,
                                       v_actual,
                                       i_actual
                                       )

                self.data["Wafer ID"].append(row["Wafer ID"])
                self.data["Field ID"].append(row["Field ID"])
                self.data["Device ID"].append(row["Device ID"])
                self.data["Set Voltage (V)"].append(v_set)
                self.data["Measured Voltage (v)"].append(v_actual)
                self.data["Measured Current (uA)"].append(i_actual * 1e3)

                self.update_test_progress()
                if self.user_requested_stop:
                    self.psu.output = 'OFF'
                    self.test_finished()
                    return