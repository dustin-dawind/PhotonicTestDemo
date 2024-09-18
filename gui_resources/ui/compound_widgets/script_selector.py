from PyQt5.QtCore import (
    pyqtSignal,
    pyqtSlot
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
    QPushButton,
    QFileDialog,
)


class ScriptSelectorUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContentsMargins(5, 5, 5, 5)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel("<u>Script Path</u>:")

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)

        self.change_script_btn = QPushButton("Change Script")


        layout.addWidget(self.label)
        layout.addWidget(self.line_edit, stretch=1)
        layout.addWidget(self.change_script_btn)


class ScriptSelector(ScriptSelectorUI):
    load_script_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.change_script_btn.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(parent=None,
                                                        caption="Select Script",
                                                        directory="",
                                                        filter="Python Files (*.py)",
                                                        options=QFileDialog.HideNameFilterDetails | QFileDialog.ReadOnly
                                                        )
        self.line_edit.setText(filepath)

    @pyqtSlot()
    def notify_script_loader(self):
        self.load_script_signal.emit(self.line_edit.text())


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = ScriptSelector()
    window.show()

    sys.exit(app.exec_())
