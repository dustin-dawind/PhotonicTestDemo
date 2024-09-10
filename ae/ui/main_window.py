from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)


class MainWindowUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Automation Examples")

        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        self.example1_btn = QPushButton("Example 1")
        self.example1_btn.setMinimumHeight(75)

        self.example2_btn = QPushButton("Example 2")
        self.example2_btn.setMinimumHeight(75)

        self.example3_btn = QPushButton("Example 3")
        self.example3_btn.setMinimumHeight(75)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(self.example1_btn)
        layout.addWidget(self.example2_btn)
        layout.addWidget(self.example3_btn)

        self.setFixedSize(300, self.minimumSizeHint().height())
