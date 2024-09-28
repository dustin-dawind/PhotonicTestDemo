import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import (
    QRectF,
    QEvent,
    pyqtSlot,
)


class BeamTraceViewerUI(pg.PlotWidget):
    def __init__(self,
                 plot_title: str,
                 x_axis_length: int,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        position_axis_title = f'Position (Pixels)'

        self.disableAutoRange(axis=pg.ViewBox.XYAxes)
        self.setAntialiasing(True)


        self.plot_area: pg.PlotDataItem = self.plot(pen=(150, 150, 150))

        self._plot_title = plot_title

        axis_padding = (x_axis_length * 0.05)
        self.setLimits(xMin=0,
                       xMax=x_axis_length + axis_padding,
                       yMin=0,
                       yMax=67000,
                       )

        self.plot_area.getViewBox().setXRange(0, x_axis_length + axis_padding, padding=0.2)
        self.plot_area.getViewBox().setYRange(0, 65536, padding=0.2)


        self.plot_item: pg.PlotItem = self.getPlotItem()
        self.plot_item.setTitle(self._plot_title)
        self.plot_item.setLabel('left', 'Intensity (a.u.)')
        self.plot_item.setLabel('bottom', position_axis_title)

        self.x_axis: pg.AxisItem = self.getAxis('bottom')
        self.x_axis.showLabel()

        self.y_axis: pg.AxisItem = self.getAxis('left')
        self.y_axis.showLabel()

    def showEvent(self, event: QEvent):
        super().showEvent(event)
        self._fit_axes_to_view()

    def resizeEvent(self, event: QEvent):
        super().resizeEvent(event)
        self._fit_axes_to_view()

    def _fit_axes_to_view(self, padding: float = 0.05):
        scene_rect = self.sceneRect()

        width = scene_rect.width() * (1 + padding)
        height = scene_rect.height()
        center = scene_rect.center()
        zoom_rect = QRectF(center.x() - width / 2, center.y() - height / 2, width, height)

        self.fitInView(zoom_rect)


class BeamTraceViewer(BeamTraceViewerUI):
    def __init__(self,
                 init_with_noise: bool = True,
                 plot_title: str = '',
                 x_axis_length: int = 640,
                 *args,
                 **kwargs
                 ):
        super().__init__(plot_title,
                         x_axis_length,
                         *args,
                         **kwargs
                         )

        self.init_with_noise = init_with_noise

        if self.init_with_noise is True:
            init_data = np.random.normal(3000, 800, x_axis_length)
            self.plot_area.setData(init_data)

    @pyqtSlot(np.ndarray)
    def update_data(self,
                    linescan_data: np.ndarray[np.uint16],
                    ):
        self.plot_area.setData(linescan_data[::-1])


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = BeamTraceViewer()
    window.show()

    sys.exit(app.exec_())
