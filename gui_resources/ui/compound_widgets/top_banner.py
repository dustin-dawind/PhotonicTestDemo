from gui_resources.ui.compound_widgets.base_widgets import (
    StartStop,
    FileSelectorObject,
    LabeledLineEdit
)
from gui_resources.ui.compound_widgets import utils

from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
)
from PyQt5.QtCore import (
    Qt
)


class TopBannerUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout()

        self.setLayout(layout)

        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

        self.test_script_selector = FileSelectorObject(parent=self,
                                                       label_base="Test Script",
                                                       file_type = "Python"
                                                       )
        self.device_definition_selector = FileSelectorObject(parent=self,
                                                             label_base="Device Definitions",
                                                             file_type="CSV"
                                                             )
        self.status_readout = LabeledLineEdit(label="<u>Status:</u>",
                                              parent=self
                                              )
        self.status_readout.text.setEnabled(False)
        self.status_readout.text.setAlignment(Qt.AlignCenter)
        self.status_readout.text.setObjectName("Status")
        utils.fix_line_edit_width(self.status_readout.text, length=10)

        self.start_stop = StartStop(parent=self)
        self.start_btn = self.start_stop.start_btn
        self.stop_btn = self.start_stop.stop_btn

        # Setting up the layout column by column
        layout.addWidget(self.test_script_selector.label, 0, 0, 1, 2)
        layout.addWidget(self.device_definition_selector.label, 1, 0, 1, 2)

        layout.addWidget(self.test_script_selector.file_path_display, 0, 2)
        layout.addWidget(self.device_definition_selector.file_path_display, 1, 2)
        layout.setColumnStretch(2, 1)

        layout.addWidget(self.test_script_selector.change_file_btn, 0, 3)
        layout.addWidget(self.device_definition_selector.change_file_btn, 1, 3)

        layout.addWidget(self.status_readout.label, 2, 4)

        layout.addWidget(self.start_btn, 0, 5, Qt.AlignCenter)
        layout.addWidget(self.stop_btn, 1, 5, Qt.AlignCenter)
        layout.addWidget(self.status_readout.text, 2, 5)


class TopBanner(TopBannerUI):
    def __init__(self, parent=None):
        super().__init__(parent)

    def update_status(self, status: str):
        self.status_readout.change_text(status)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = TopBanner()
    window.show()

    sys.exit(app.exec_())


