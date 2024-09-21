from PyQt5.QtCore import (
    QThread,
    QObject, pyqtSignal,
)

from instruments.instrument_emulators.abc import AbstractEmulator


class InstrumentError(Exception):
    pass


class CommunicationHandler(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.emulator = None
        self.instrument_thread = QThread(parent=parent)

        self.connected = False

    def query(self, command: str):
        if self.connected:
            try:
                self.emulator.query(command)
            except KeyError:
                raise InstrumentError(f"No response from instrument. command: {command}")
            else:
                QThread.msleep(AbstractEmulator._timer_interval + 20)
                return self.emulator.get_response_buffer()

    def write(self, command: str):
        if self.connected:
            if " " not in command:
                if command == "*RST":
                    self.emulator.reset()
            else:
                if len(split_command := command.split(" ")) > 2:
                    raise InstrumentError(f"Invalid command: {command}")

                setting, value = split_command
                self.emulator.write(setting, value)

    def connect(self, emulator: AbstractEmulator):
        if not self.connected:
            try:
                self._register_emulator(emulator)
            except KeyError:
                raise ConnectionError(f"Error connecting to instrument emulator: {emulator}")
            else:
                self.connected = True

    def disconnect(self):
        if self.connected:
            self.instrument_thread.exit()
            self.connected = False

    def _register_emulator(self, emulator: QObject):
        self.emulator = emulator
        self.emulator.moveToThread(self.instrument_thread)
        self.instrument_thread.started.connect(self.emulator.start_polling)
        self.instrument_thread.finished.connect(self.emulator.stop_polling)
        self.instrument_thread.start()

