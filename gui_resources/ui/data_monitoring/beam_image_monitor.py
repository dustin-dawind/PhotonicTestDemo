from PyQt5.QtWidgets import (
    QWidget
)


class PlaceHolder(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys


    app = QApplication(sys.argv)

    window = PlaceHolder()
    window.show()

    sys.exit(app.exec_())
