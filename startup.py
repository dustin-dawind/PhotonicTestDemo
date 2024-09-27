import sys
import os

os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

from gui_resources import MainWindow
from PyQt5.QtWidgets import QApplication


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec_())
