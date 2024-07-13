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

        drag_rect = QRectF(0, 0, self.boundingRect().width() - 120, self.boundingRect().height())
        painter.fillRect(drag_rect, QBrush(QColor(100, 200, 255)))

        painter.setPen(QColor(0, 0, 0))
        painter.drawText(drag_rect, Qt.AlignmentFlag.AlignCenter, "Drag Here")

        clone_rect = QRectF(self.boundingRect().width() - 120, 0, 60, self.boundingRect().height())
        painter.fillRect(clone_rect, QBrush(QColor(180, 180, 180)))
        painter.drawText(clone_rect, Qt.AlignmentFlag.AlignCenter, "Clone")

        delete_rect = QRectF(self.boundingRect().width() - 60, 0, 60, self.boundingRect().height())
        painter.fillRect(delete_rect, QBrush(QColor(255, 100, 100)))
        painter.drawText(delete_rect, Qt.AlignmentFlag.AlignCenter, "Delete")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            clone_rect = QRectF(self.boundingRect().width() - 120, 0, 60, self.boundingRect().height())
            delete_rect = QRectF(self.boundingRect().width() - 60, 0, 60, self.boundingRect().height())
            if clone_rect.contains(event.pos()):
                self.cloneRequested.emit()
            elif delete_rect.contains(event.pos()):
                self.deleteRequested.emit()
            else:
                super().mousePressEvent(event)

