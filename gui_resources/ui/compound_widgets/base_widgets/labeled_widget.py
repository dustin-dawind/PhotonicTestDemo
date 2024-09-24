from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit
)


class LabeledWidget(QWidget):
    def __init__(self,
                 widget: QWidget,
                 label: str,
                 parent=None
                 ):
        super().__init__(parent=parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(label)

        if isinstance(widget, type):  # Will return True if widget is an uninstantiated class
            raise TypeError("Widget must be an instance of a class that inherit from or be a QWidget")
        else:
            self.widget = widget

        layout.addWidget(self.label)
        layout.addWidget(self.widget)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    window = LabeledWidget(QLabel("Second Test Label"), "<u>Test Label:</u>")
    window.show()

    sys.exit(app.exec_())
