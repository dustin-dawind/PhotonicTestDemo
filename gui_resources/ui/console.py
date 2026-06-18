# import logging
# from PyQt6.QtWidgets import (
#     QWidget,
#     QTextEdit,
#     QFrame, QVBoxLayout
# )
#
# class GuiLogger(logging.Handler):
#     def __init__(self):
#         super().__init__()
#         self.edit = Console()
#
#     def log(self, record):
#         self.edit.append_line(self.format(record))  # implementation of append_line omitted
#
# log = logging.getLogger()
# log.addHandler(GuiLogger())
#
#
# class Console(QFrame):
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#
#         layout = QVBoxLayout()
#         self.setLayout(layout)
#
#         self.text_edit = QTextEdit()
#         self.text_edit.setReadOnly(True)
#
#         self.setFrameShape(QFrame.Box | QFrame.Sunken)
#
#         layout.addWidget(self.text_edit)
#
#
# if __name__ == "__main__":
#     from PyQt6.QtWidgets import QApplication
#     import sys
#
#     app = QApplication(sys.argv)
#
#     window = Console()
#     window.show()
#
#     log.
#
#     sys.exit(app.exec_())
