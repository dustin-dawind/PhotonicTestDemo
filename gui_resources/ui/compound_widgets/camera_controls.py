from gui_resources.ui.compound_widgets import utils

from gui_resources.ui.compound_widgets.base_widgets import (
    MinMaxSliderObject,
    UnderlinedLabel,
)

from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QFrame
)


class CameraControls(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.min_column_text = UnderlinedLabel(label="Min",
                                               parent=self
                                               )
        self.max_column_text = UnderlinedLabel(label="Max",
                                               parent=self
                                               )
        self.position_column_text = UnderlinedLabel(label="Current",
                                                    parent=self
                                                    )

        self.int_time_controls = MinMaxSliderObject(label="Integration Time (ms):",
                                                    min_value=0.1,
                                                    max_value=10,
                                                    parent=self
                                                    )
        self.gain_controls = MinMaxSliderObject(label="Gain:",
                                                min_value=1,
                                                max_value=3,
                                                parent=self
                                                )
        self.offset_controls = MinMaxSliderObject(label="Offset:",
                                                  min_value=0,
                                                  max_value=5000,
                                                  parent=self
                                                  )

        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

        self.int_time_controls.fix_line_edit_width(length=8)
        self.gain_controls.fix_line_edit_width(length=8)
        self.offset_controls.fix_line_edit_width(length=8)

        frame = QFrame()
        frame.setObjectName("CameraControlsBorder")
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("QFrame#CameraControlsBorder"
                            "{"
                            "border: 1px solid black;"
                            "border-radius: 5px;"
                            "}")

        frame_layout = QHBoxLayout()
        frame_layout.addWidget(frame)

        self.setLayout(frame_layout)

        layout = QGridLayout()
        frame.setLayout(layout)

        # Setting up the layout column by column
        layout.addWidget(self.int_time_controls.label, 1, 0)
        layout.addWidget(self.gain_controls.label, 2, 0)
        layout.addWidget(self.offset_controls.label, 3, 0)

        layout.addWidget(self.min_column_text, 0, 1)
        layout.addWidget(self.int_time_controls.min_display, 1, 1)
        layout.addWidget(self.gain_controls.min_display, 2, 1)
        layout.addWidget(self.offset_controls.min_display, 3, 1)

        layout.addWidget(self.int_time_controls.slider, 1, 2)
        layout.addWidget(self.gain_controls.slider, 2, 2)
        layout.addWidget(self.offset_controls.slider, 3, 2)

        layout.addWidget(self.max_column_text, 0, 3)
        layout.addWidget(self.int_time_controls.max_display, 1, 3)
        layout.addWidget(self.gain_controls.max_display, 2, 3)
        layout.addWidget(self.offset_controls.max_display, 3, 3)

        layout.addWidget(self.position_column_text, 0, 4)
        layout.addWidget(self.int_time_controls.position_display, 1, 4)
        layout.addWidget(self.gain_controls.position_display, 2, 4)
        layout.addWidget(self.offset_controls.position_display, 3, 4)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = CameraControls()
    window.show()

    sys.exit(app.exec_())
