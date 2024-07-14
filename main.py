import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("resources/icon.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
