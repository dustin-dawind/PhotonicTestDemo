from instruments.instrument_wrappers import (
    camera,
    power_meter,
    psu
)
from instruments.instrument_emulators import (
    CameraEmulator,
    PSUEmulator,
    PowerMeterEmulator,
    LaserEmulator
)

from PyQt5.QtCore import (
    QThread,
    QObject
)


class InstrumentRegistry(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.psu_emulator = PSUEmulator()
        self.camera_emulator = CameraEmulator()
        self.power_meter_emulator = PowerMeterEmulator()

        # Laser emulator needs to have its thread started here since it doesn't have a "driver" wrapper to handle its thread
        self.laser_emulator = LaserEmulator()
        self._laser_emulator_thread = QThread(parent=self)
        self.laser_emulator.moveToThread(self._laser_emulator_thread)
        self._laser_emulator_thread.start()

        # Connect instruments to their emulators. The GUI will control the emulators via these "driver" interfaces
        self.camera = camera.Instrument()
        self.camera.connect(self.camera_emulator)

        self.power_meter = power_meter.Instrument()
        self.power_meter.connect(self.power_meter_emulator)

        self.psu = psu.Instrument()
        self.psu.connect(self.psu_emulator)

        self.psu_emulator.output_changed.connect(self.laser_emulator.psu_status_changed)
        self.psu_emulator.i_current_changed.connect(self.laser_emulator.update_power)
        self.psu_emulator.request_voltage.connect(self.laser_emulator.update_voltage)

        self.laser_emulator.voltage_value_ready.connect(self.psu_emulator.update_voltage)
        self.laser_emulator.power_value_ready.connect(self.power_meter_emulator.base_power_changed)

    def stop_threads(self):
        self._laser_emulator_thread.exit()
        self.camera.disconnect()
        self.psu.disconnect()
        self.power_meter.disconnect()


if __name__ == "__main__":
    all_instruments = InstrumentRegistry()


