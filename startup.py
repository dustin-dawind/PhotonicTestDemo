import sys
import os
from pathlib import Path

# Need to set this environment variable before importing any module that depends on pyqtgraph. This is because
# matplotlib lists pyside6 as one of its dependencies, and as such is installed with matplotlib automatically. This
# means that the environment has both PyQt5 and PySide6 installed. pyqtgraph tries to auto-detect which package to use,
# and tries PySide6 first, so we need to explicitly tell it to use PyQt5
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt6'

from gui_resources import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

try:
    import pyi_splash
except ModuleNotFoundError:
    pass
else:
    import time
    pyi_splash.update_text("Done!")
    time.sleep(2)
    pyi_splash.close()


if getattr(sys, 'frozen', False):
    cwd = Path(sys._MEIPASS)
else:
    cwd = Path.cwd()


app = QApplication(sys.argv)
app.setWindowIcon(QIcon(str(cwd / "resources\\logo.jpg")))
window = MainWindow()
window.show()

sys.exit(app.exec_())
