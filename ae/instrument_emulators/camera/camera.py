from ae.instrument_emulators import AbstractInstrument

class Instrument(AbstractInstrument, Camera):
    def __init__(self, handle):
        ...