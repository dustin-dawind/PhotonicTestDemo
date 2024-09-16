import sys
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg

class LIVDataMonitorUI(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.plotItem.setTitle("Real Time Data Monitor")
        self.plotItem.showAxis('right')

        self.plotItem.getAxis('right').setLabel(text="Voltage", units="V")
        self.plotItem.getAxis('left').setLabel(text="Power", units="W")

        self.plotItem.addLegend(offset=(10,10))
        self.setBackground('w')


if __name__ == "__main__":


    app = QApplication(sys.argv)

    window = LIVDataMonitorUI()
    window.show()

    sys.exit(app.exec_())






