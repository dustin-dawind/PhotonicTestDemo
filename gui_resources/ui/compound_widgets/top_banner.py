from gui_resources.ui.compound_widgets.base_widgets import (
    StartStop,
    FileSelectorObject,
    )

from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QProgressBar
)
from PyQt5.QtCore import (
    Qt,
    pyqtSlot
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
                                                       file_type="Python"
                                                       )
        self.device_definition_selector = FileSelectorObject(parent=self,
                                                             label_base="Device Definitions",
                                                             file_type="CSV"
                                                             )
        self.progress_readout = QProgressBar(parent=self)
        # self.progress_readout = LabeledWidget(widget=QProgressBar(parent=self),
        #                                       label="<u>Progress:</u>",
        #                                       parent=self
        #                                       )
        # self.progress_readout.widget.setEnabled(False)
        # self.progress_readout.widget.setFormat("Idle")
        self.progress_readout.setTextVisible(True)
        self.progress_readout.setValue(0)
        self.progress_readout.setFormat("No Test Running")
        self.progress_readout.setObjectName("TestProgress")
        self.progress_readout.setStyleSheet("QProgressBar#TestProgress {"
                                            "border: 1px solid grey;"
                                            # "border-radius: 5px;"
                                            "background-color: white;"
                                            "text-align: center;"
                                            "}"
                                            # "QProgressBar#TestProgress::chunk {"
                                            # ""
                                            # "border-radius: 5px;"
                                            # # "border-bottom-left-radius: 5px;"
                                            # "}"
                                            )

        self.start_stop = StartStop(parent=self)
        self.start_btn = self.start_stop.start_btn
        self.stop_btn = self.start_stop.stop_btn

        # Setting up the layout column by column
        layout.addWidget(self.test_script_selector.label, 0, 0)
        layout.addWidget(self.device_definition_selector.label, 1, 0)

        layout.addWidget(self.test_script_selector.file_path_display, 0, 1)
        layout.addWidget(self.device_definition_selector.file_path_display, 1, 1)
        layout.setColumnStretch(1, 1)

        layout.addWidget(self.test_script_selector.change_file_btn, 0, 2)
        layout.addWidget(self.device_definition_selector.change_file_btn, 1, 2)
        # layout.addWidget(self.progress_readout.label, 2, 3)

        layout.addWidget(self.progress_readout, 2, 2, 1, 2)

        # layout.addWidget(self.start_stop, 0, 3, 2, 1)

        layout.addWidget(self.start_btn, 0, 3, Qt.AlignCenter)
        layout.addWidget(self.stop_btn, 1, 3, Qt.AlignCenter)


class TopBanner(TopBannerUI):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.test_script_selector.selected_file_changed.connect(self.set_progress_no_test)
        self.device_definition_selector.selected_file_changed.connect(self.set_progress_no_test)

    def set_progress_maximum(self,
                             max_value: int
                             ):
        self.progress_readout.setRange(0,
                                       max_value
                                       )

    def update_progress_value(self, value: int):
        self.progress_readout.setFormat("%p% (%v/%m)")
        self.progress_readout.setValue(value)

    def change_progress_status(self, text: str):
        self.progress_readout.setFormat(text)

    def set_progress_no_test(self):
        self.progress_readout.reset()
        self.progress_readout.setValue(0)
        self.progress_readout.setFormat("No Test Running")

    @pyqtSlot()
    def disable_file_selection(self):
        self.test_script_selector.change_file_btn.setEnabled(False)
        self.device_definition_selector.change_file_btn.setEnabled(False)

    @pyqtSlot()
    def enable_file_selection(self):
        self.test_script_selector.change_file_btn.setEnabled(True)
        self.device_definition_selector.change_file_btn.setEnabled(True)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = TopBanner()
    window.show()

    sys.exit(app.exec_())


