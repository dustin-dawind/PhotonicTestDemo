import sys
from pathlib import Path
from typing import Literal

from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QWidget,
    QPushButton,
    QFileDialog,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal
)

# Check if the script is being run in a frozen environment (e.g. as an executable)
is_frozen = getattr(sys, 'frozen', False)
if is_frozen:
    base_path = Path(sys._MEIPASS)
elif 'Quintessent' not in str(Path.cwd().parent):
    base_path = Path.cwd()
else:
    base_path = Path.cwd().parents[3]

PATH_TO_TEST_SCRIPTS = str(base_path / "live_testing")


class FileSelectorUINoLayout(QWidget):
    def __init__(self,
                 label_base: str,
                 parent=None
                 ):
        super().__init__(parent)

        # self.setContentsMargins(5, 5, 5, 5)
        # layout = QHBoxLayout()
        # self.setLayout(layout)

        self.label = QLabel(f"<u>{label_base} Path</u>:")
        self.label.setAlignment(Qt.AlignRight)

        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)

        self.change_file_btn = QPushButton(f"Change {label_base}")

        # layout.addWidget(label)
        # layout.addWidget(self.script_path_display, stretch=1)
        # layout.addWidget(self.change_script_btn)


class FileSelectorObject(FileSelectorUINoLayout):
    selected_file_changed = pyqtSignal()

    def __init__(self,
                 label_base: str,
                 file_type: Literal["Python", "CSV"] = "Python",
                 parent=None
                 ):
        super().__init__(parent=parent,
                         label_base=label_base
                         )
        match file_type:
            case "Python":
                self._file_filter = "Python Files (*.py)"
            case "CSV":
                self._file_filter = "CSV Files (*.csv)"
            case _:
                raise ValueError(f"Invalid file type: {file_type}. Must be 'Python' or 'CSV'")

        self.label_base = label_base

        self.change_file_btn.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(parent=None,
                                                  caption=f"Select {self.label_base} File",
                                                  directory=PATH_TO_TEST_SCRIPTS,
                                                  filter=self._file_filter,
                                                  options=QFileDialog.HideNameFilterDetails | QFileDialog.ReadOnly
                                                  )
        self.file_path_display.setText(filepath)
        self.selected_file_changed.emit()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)

    window = FileSelectorObject("Test")
    window.show()

    sys.exit(app.exec_())
