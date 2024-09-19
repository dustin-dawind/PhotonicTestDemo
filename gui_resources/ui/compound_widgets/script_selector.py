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

# Check if the script is being run in a frozen environment (e.g. as an executable)
is_frozen = getattr(sys, 'frozen', False)
if is_frozen:
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path.cwd().parents[3]

PATH_TO_TEST_SCRIPTS = base_path / "test_scripts"


class ScriptSelectorUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContentsMargins(5, 5, 5, 5)

        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel("<u>Script Path</u>:")

        self.script_path_display = QLineEdit()
        self.script_path_display.setReadOnly(True)

        self.change_script_btn = QPushButton("Change Script")


        layout.addWidget(label)
        layout.addWidget(self.script_path_display, stretch=1)
        layout.addWidget(self.change_script_btn)


class ScriptSelector(ScriptSelectorUI):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.change_script_btn.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(parent=None,
                                                        caption="Select Script",
                                                        directory=PATH_TO_TEST_SCRIPTS,
                                                        filter="Python Files (*.py)",
                                                        options=QFileDialog.HideNameFilterDetails | QFileDialog.ReadOnly
                                                        )
        self.script_path_display.setText(filepath)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = ScriptSelector()
    window.show()

    sys.exit(app.exec_())
