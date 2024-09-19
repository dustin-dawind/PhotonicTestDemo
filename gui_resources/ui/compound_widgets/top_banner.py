from gui_resources.ui.compound_widgets import (
    StartStop,
    ScriptSelector
)

from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout
)

class TopBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

        self.script_selector = ScriptSelector()

        start_stop = StartStop()
        self.start_btn = start_stop.start_btn
        self.stop_btn = start_stop.stop_btn

        layout.addWidget(self.script_selector, stretch=1)
        layout.addWidget(self.start_stop)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = TopBarUI()
    window.show()

    sys.exit(app.exec_())


