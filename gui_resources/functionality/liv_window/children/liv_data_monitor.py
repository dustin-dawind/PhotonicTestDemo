from gui_resources.ui.liv_window.children import LIVDataMonitorUI

class LIVDataMonitor(LIVDataMonitorUI):
    def __init__(self, parent=None):
        super().__init__(parent)

    def clear_data(self):
        self.plotItem.plot(clear=True)
