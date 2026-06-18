import numpy as np
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import pyqtSlot
import pyqtgraph as pg


class BeamHistogramPlot(pg.PlotWidget):

    def __init__(self,
                 *args,
                 **kwargs
                 ):
        super().__init__(*args,
                         **kwargs
                         )

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.num_bins = 65536 // 512
        self.num_pixels = 640 * 512
        self.plot_area = self.plot()

        plot_item = self.getPlotItem()
        plot_item.setTitle("Histogram")
        plot_item.setLabel('left', '# of Pixels')
        plot_item.setLabel('bottom', 'Pixel Intensity (a.u.)')

        self.setLimits(xMin=0, xMax=65536 - 1 + 6144, yMin=0, yMax=self.num_pixels, minXRange=10000,
                       minYRange=10)
        self.plot_area.getViewBox().setXRange(min=0, max=65536 - 1 + 6144, padding=0.2)
        self.plot_area.getViewBox().setYRange(min=0, max=self.num_pixels, padding=0.2)
        x_axis = self.getAxis('bottom')
        x_axis.setTickSpacing(levels=[(65536 // 4, 0), (65536 // 16, 0)])
        x_axis.showLabel()
        y_axis = self.getAxis('left')
        y_axis.setTickSpacing(
            levels=[(self.num_pixels // 2, 0), (self.num_pixels // 4, 0), (self.num_pixels // 8, 0)])
        y_axis.showLabel()
        self.disableAutoRange(axis=pg.ViewBox.XYAxes)
        self.setAntialiasing(True)

    @pyqtSlot(np.ndarray)
    def update_data(self, pixel_data: np.ndarray[np.uint16]):
        new_data = pixel_data.ravel()
        freq, bin_edges = np.histogram(new_data, bins=self.num_bins)

        # This should allow the plot to be updated without having to re-link the axes every time
        self.plot_area.setData(bin_edges, freq, fillLevel=0, stepMode="center", brush=(0, 0, 255, 150))


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = BeamHistogramPlot()
    window.show()

    sys.exit(app.exec_())
