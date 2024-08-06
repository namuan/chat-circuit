from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsView


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Create instruction text item
        self.instruction_text = "Command/Ctrl + Click to create node"
        self.instruction_font = QFont("Arial", 16, QFont.Weight.Bold)
        self.text_color = QColor(100, 100, 100, 255)
        self.bg_color = QColor(0, 0, 0, 50)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        self.drawForeground(painter, QRectF(self.viewport().rect()))
        painter.end()

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        # Draw instruction label
        painter.setFont(self.instruction_font)
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(self.instruction_text)
        text_height = fm.height()

        # Calculate text position
        padding = 10
        text_rect = QRectF(
            padding, padding, text_width + 2 * padding, text_height + 2 * padding
        )

        # Draw background
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(text_rect, 5, 5)

        # Draw text
        painter.setPen(self.text_color)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.instruction_text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.viewport().update()
