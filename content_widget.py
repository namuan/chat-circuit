from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QGraphicsWidget


class ContentWidget(QGraphicsWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(100)

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(QColor(255, 255, 255)))
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, "Content")
