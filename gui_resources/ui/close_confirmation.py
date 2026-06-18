from PyQt6.QtWidgets import QMessageBox


class CloseConfirmation(QMessageBox):
    def __init__(self,
                 parent=None,
                 **kwargs
                 ):
        super().__init__(QMessageBox.Icon.Question,
                         "Automation Examples",
                         "Are you sure you want to quit?",
                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                         parent=parent,
                         **kwargs
                         )
        font = self.font()
        font.setPointSize(14)
        self.setFont(font)

        self.setEscapeButton(QMessageBox.StandardButton.No)
        self.setDefaultButton(QMessageBox.StandardButton.No)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = CloseConfirmation()
    window.show()
    sys.exit(app.exec())


