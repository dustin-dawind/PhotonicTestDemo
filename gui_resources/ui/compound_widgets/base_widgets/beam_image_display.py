import pyqtgraph as pg


class BeamImageDisplay(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.plotItem.showAxes(False)
        self.setBackground('w')


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = BeamImageDisplay()
    window.show()

    sys.exit(app.exec_())
