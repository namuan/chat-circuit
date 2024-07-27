import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from main_window import MainWindow
import faulthandler

faulthandler.enable()
faulthandler.dump_traceback(open("crash.log", "w"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("resources/icon.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
