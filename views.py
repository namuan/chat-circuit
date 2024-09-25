from PyQt6.QtCore import QSize, pyqtSignal, QPointF, QTimer
from PyQt6.QtCore import Qt, QRectF, QPoint, QRect
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtWidgets import QGraphicsView, QRubberBand

from minimap import MiniMap


class CustomGraphicsView(QGraphicsView):
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Create instruction text item
        self.instruction_text = "\nCommand/Ctrl + Click to create node"
        self.instruction_text += "\nDrag node by using the blue circle"
        self.instruction_text += "\nHold Shift + Click and drag to select and zoom"
        self.instruction_font = QFont("Arial", 16, QFont.Weight.Bold)
        self.text_color = QColor(100, 100, 100, 255)
        self.bg_color = QColor(0, 0, 0, 50)

        # Zoom selection variables
        self.rubberBand = None
        self.origin = QPoint()
        self.is_selecting = False

        # Create mini-map
        self.minimap = MiniMap(self)
        self.minimap.setParent(self.viewport())
        self.minimap.hide()  # Hide initially, show after the first resizeEvent

        # Update mini-map periodically
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_minimap)
        self.update_timer.start(100)  # Update every 100 ms

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        self.drawForeground(painter, QRectF(self.viewport().rect()))
        painter.end()

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        if rect.topLeft() != QPointF(0, 0):
            return

        # Draw instruction label
        painter.setFont(self.instruction_font)
        fm = painter.fontMetrics()
        text_width = max(
            fm.horizontalAdvance(line) for line in self.instruction_text.split("\n")
        )
        text_height = fm.height() * len(self.instruction_text.split("\n"))

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
        y = int(text_rect.top() + padding)
        for line in self.instruction_text.split("\n"):
            painter.drawText(int(text_rect.left() + padding), y, line)
            y += fm.height()

    def mousePressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.is_selecting = True
            self.origin = event.pos()
            if not self.rubberBand:
                self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()))
        else:
            super().mouseMoveEvent(event)
        self.minimap.update_minimap()

    def mouseReleaseEvent(self, event):
        if self.is_selecting:
            self.is_selecting = False
            if self.rubberBand:
                self.rubberBand.hide()
                selection_polygon = self.mapToScene(self.rubberBand.geometry())
                selection_rect = selection_polygon.boundingRect()
                self.zoomToRect(selection_rect)
        else:
            super().mouseReleaseEvent(event)
        self.update_minimap()

    def zoomToRect(self, rect):
        if not rect.isEmpty():
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.updateSceneRect(self.sceneRect().united(rect))
            self.updateZoomFactor()
            self.update_minimap()

    def update_minimap(self):
        if self.minimap.isVisible():
            self.minimap.update_minimap()

    def updateZoomFactor(self):
        current_transform = self.transform()
        current_scale = current_transform.m11()  # Horizontal scale factor
        self.zoomChanged.emit(current_scale)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.minimap.setGeometry(10, self.height() - 160, 200, 150)
        self.minimap.show()
        self.viewport().update()
