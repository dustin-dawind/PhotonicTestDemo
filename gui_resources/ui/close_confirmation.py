from PyQt5.QtWidgets import QMessageBox


class CloseConfirmation(QMessageBox):
    def __init__(self,
                 parent=None,
                 **kwargs
                 ):
        super().__init__(QMessageBox.Question,
                         "Automation Examples",
                         "Are you sure you want to quit?",
                         QMessageBox.Yes | QMessageBox.No,
                         parent=parent,
                         **kwargs
                         )
        font = self.font()
        font.setPointSize(14)
        self.setFont(font)

        self.setEscapeButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)


