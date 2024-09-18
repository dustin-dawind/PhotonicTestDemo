from PyQt5.QtCore import (
    QThread,
    QObject,
)

from instruments.instrument_emulators.abc import AbstractEmulator


class InstrumentError(Exception):
    pass


class CommunicationHandler:
    def __init__(self):
        super().__init__()

        self.emulator = None
        self.instrument_thread = QThread()

        self.connected = False

    def query(self, command: str):
        if self.connected:
            try:
                self.emulator.query(command)
            except KeyError:
                raise InstrumentError(f"No response from instrument. command: {command}")
            else:
                QThread.msleep(50)
                return self.emulator.get_response_buffer()

    def write(self, command: str):
        if self.connected:
            if " " not in command:
                if command == "*RST":
                    self.emulator.reset()
            else:
                if len(split_command :=  command.split(" ")) > 2:
                    raise InstrumentError(f"Invalid command: {command}")

                setting, value = split_command
                self.emulator.write(setting, value)

    def connect(self, emulator: AbstractEmulator):
        if not self.connected:
            try:
                self._register_emulator(emulator)
            except KeyError:
                raise ConnectionError(f"F")
            else:
                self.connected = True

    def disconnect(self):
        if self.connected:
            self.emulator = None
            self.connected = False

    def _register_emulator(self, emulator: QObject):
        self.emulator = emulator
        self.emulator.moveToThread(self.instrument_thread)
        self.instrument_thread.start()


# #TODO: instantiate this class in each emulator's __init__
# class ConnectionHandler:
#     def __init__(self,  handle: str):
#
#         self.delegate = CommunicationDelegate(handle)
#         self.delegate_thread = QThread()
#         self.delegate.moveToThread(self.delegate_thread)
#         self.delegate_thread.start()
#
#     def __getattr__(self, attr):  # Implicitly wrap methods from delegate (inspired by pyqtgraph.widgets.PlotWidget)
#         if hasattr(self.delegate, attr):
#             method = getattr(self.delegate, attr)
#             if hasattr(method, '__call__'):
#                 return method
#         raise AttributeError(attr)

