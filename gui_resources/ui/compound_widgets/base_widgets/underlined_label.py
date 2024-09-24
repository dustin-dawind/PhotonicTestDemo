from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy
)
from PyQt5.QtCore import (
    Qt
)


class UnderlinedLabel(QWidget):
    def __init__(self,label="", parent=None):
        super().__init__(parent=parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        label = QLabel(label)
        label.setAlignment(Qt.AlignCenter)

        underline = QFrame()
        underline.setFrameShape(QFrame.HLine)

        layout.addWidget(label)
        layout.addWidget(underline)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = UnderlinedLabel("Test Label")
    window.show()

    sys.exit(app.exec_())
