from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit
)


class LabeledLineEdit(QWidget):
    def __init__(self, label: str,
                 parent=None
                 ):
        super().__init__(parent=parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(label)
        self.text = QLineEdit()
        self.default_text_style = self.text.styleSheet()

        layout.addWidget(self.label)
        layout.addWidget(self.text)

    def change_text(self, text: str):
        self.text.setText(text)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = LabeledLineEdit("<u>Test Label:</u>")
    window.show()

    sys.exit(app.exec_())
