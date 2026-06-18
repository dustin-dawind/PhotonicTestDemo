import numpy as np
from PyQt6.QtGui import (
    QColor,
    QPen
)
from PyQt6.QtCore import (
    pyqtSlot,
    Qt,
    QPointF
)
import pyqtgraph as pg


pg.setConfigOption('useNumba', True)


class BeamImageDisplayUI(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.data = np.zeros((640,
                              512
                              ),
                             dtype=np.uint16
                             )

        self.image_item = pg.ImageItem(autoLevels=False, axisOrder='row-major')

        plot_item = self.getPlotItem()
        plot_item.setAspectLocked()
        plot_item.showAxes(False)
        self.setBackground('w')

        column_idx = 640 / 2
        row_idx = 512 / 2

        self.column_trace_marker = pg.InfiniteLine(pos=column_idx, angle=90, pen='r')
        self.row_trace_marker = pg.InfiniteLine(pos=row_idx, angle=0, pen='r')

        marker_color = QColor(Qt.darkYellow)
        marker_color.setAlphaF(0.5)
        marker_pen = QPen(marker_color)
        marker_pen.setStyle(Qt.PenStyle.DashLine)

        self.column_trace_marker.setPen(marker_pen)
        self.row_trace_marker.setPen(marker_pen)

        self.column_trace_marker.setVisible(False)
        self.row_trace_marker.setVisible(False)

        self.view_box = self.plotItem.getViewBox()

        self.pixel_peaker = pg.TargetItem(pos=(0, 0),
                                          symbol='o',
                                          size=5,
                                          movable=False,
                                          pen='r',
                                          brush='r',
                                          )
        self.pixel_peaker.setVisible(False)

        self.addItem(self.image_item)
        self.addItem(self.column_trace_marker)
        self.addItem(self.row_trace_marker)
        self.addItem(self.pixel_peaker)


class BeamImageDisplay(BeamImageDisplayUI):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.image_item.setImage(np.zeros((512, 640), dtype=np.uint16) + 5000, autoLevels=False)

        self.plotItem.scene().sigMouseMoved.connect(self.mouse_moved)

    def mouse_moved(self, pos: QPointF):
        if not self.plotItem.sceneBoundingRect().contains(pos):
            if self.pixel_peaker.isVisible():
                self.pixel_peaker.setVisible(False)
        else:
            mouse_point = self.view_box.mapSceneToView(pos)
            x_idx = round(mouse_point.x())
            y_idx = round(mouse_point.y())
            x_lim, y_lim = self.data.shape
            if 0 < x_idx < x_lim and 0 < y_idx < y_lim:
                if not self.pixel_peaker.isVisible():
                    self.pixel_peaker.setVisible(True)
                self.pixel_peaker.setPos(x_idx, y_idx)
                value = self.data[x_idx, y_idx]
                self.pixel_peaker.setLabel(str(value),
                                           labelOpts={'color'         : 'r',
                                                      'offset'        : (-5, -10),
                                                      'ensureInBounds': True
                                                      }
                                           )
            else:
                if self.pixel_peaker.isVisible():
                    self.pixel_peaker.setVisible(False)

    def show_trace_markers(self):
        self.column_trace_marker.setVisible(True)
        self.row_trace_marker.setVisible(True)

    def hide_trace_markers(self):
        self.column_trace_marker.setVisible(False)
        self.row_trace_marker.setVisible(False)

    @pyqtSlot(np.ndarray, dict)
    def update_image(self,
                     image: np.ndarray,
                     central_lobe_xy: dict[str, int],
                     ):
        self.image_item.setImage(image,
                                 axis_order='row-major',
                                 autoLevels=False
                                 )
        self.data = image

        self.column_trace_marker.setPos(central_lobe_xy["x"])
        self.row_trace_marker.setPos(central_lobe_xy["y"])


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = BeamImageDisplay()
    window.show()

    sys.exit(app.exec_())
