from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPushButton,
    QSizePolicy
)


class StartStopUI(QWidget):
    def __init__(self,
                 start_text,
                 stop_text,
                 parent=None
                 ):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)


        self.start_btn = QPushButton(start_text)
        self.start_btn.setSizePolicy(QSizePolicy.Maximum, self.start_btn.sizePolicy().verticalPolicy())

        self.stop_btn = QPushButton(stop_text)
        self.stop_btn.setSizePolicy(QSizePolicy.Maximum, self.start_btn.sizePolicy().verticalPolicy())
        self.stop_btn.setEnabled(False)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)


class StartStop(StartStopUI):
    def __init__(self,
                 parent=None,
                 start_text="Start Test",
                 stop_text="Stop Test"
                 ):
        super().__init__(parent=parent,
                         start_text=start_text,
                         stop_text=stop_text
                         )

        self.start_btn.clicked.connect(self.toggle_enabled_button)
        self.stop_btn.clicked.connect(self.toggle_enabled_button)

    def toggle_enabled_button(self):
        if self.start_btn.isEnabled():
            self.stop_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
        else:
            self.stop_btn.setEnabled(False)
            self.start_btn.setEnabled(True)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = StartStop()
    window.show()

    sys.exit(app.exec_())