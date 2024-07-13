from PyQt6.QtWidgets import QGraphicsWidget
from PyQt6.QtCore import pyqtSignal, Qt, QRectF
from PyQt6.QtGui import QColor, QBrush


class HeaderWidget(QGraphicsWidget):
    cloneRequested = pyqtSignal()
    deleteRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(QColor(200, 200, 200)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
