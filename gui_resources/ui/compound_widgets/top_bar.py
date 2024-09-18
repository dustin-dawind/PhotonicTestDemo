from gui_resources.ui.compound_widgets import (
    StartStop,
    ScriptSelector
)

from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout
)

class TopBarUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

        self.test_script_path = ScriptSelector()
        self.start_stop = StartStop()

        layout.addWidget(self.test_script_path, stretch=1)
        layout.addWidget(self.start_stop)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = TopBarUI()
    window.show()

    sys.exit(app.exec_())


