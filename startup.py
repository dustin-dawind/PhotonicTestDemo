import sys
import os

from PyQt5.QtGui import QIcon

os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

from gui_resources import MainWindow
from PyQt5.QtWidgets import QApplication


app = QApplication(sys.argv)
app.setWindowIcon(QIcon("logo.jpg"))
window = MainWindow()
window.show()

sys.exit(app.exec_())
