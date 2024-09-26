from PyQt6.QtCore import (
    QSize,
    pyqtSignal,
    QPointF,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
)
from PyQt6.QtCore import Qt, QRectF, QPoint, QRect
from PyQt6.QtGui import QFont, QColor, QPainter, QFontMetrics
from PyQt6.QtWidgets import QGraphicsView, QRubberBand, QScrollBar

from minimap import MiniMap
from PyQt6.QtGui import QTransform


class CustomGraphicsView(QGraphicsView):
    zoomChanged = pyqtSignal(float)

    def __init__(self, scene, initial_zoom=1.0):
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
        self.icon_color = QColor(255, 255, 255)  # White color for the icon

        # Zoom selection variables
        self.rubberBand = None
        self.origin = QPoint()
        self.is_selecting = False

        # Create mini-map
        self.minimap = MiniMap(self)
        self.minimap.setParent(self.viewport())
        self.minimap.hide()  # Hide initially, show after the first resizeEvent

        # Set minimum and maximum zoom levels
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_zoom = initial_zoom

        # Create zoom scroll bar
        self.zoom_scrollbar = QScrollBar(Qt.Orientation.Horizontal, self)
        self.zoom_scrollbar.setRange(0, 100)
        initial_scrollbar_value = int(
            ((self.current_zoom - self.min_zoom) / (self.max_zoom - self.min_zoom))
            * 100
        )
        self.zoom_scrollbar.setValue(initial_scrollbar_value)
        self.zoom_scrollbar.valueChanged.connect(self.zoom_scrollbar_changed)

        # Apply initial zoom
        self.zoom_to(self.current_zoom)

        # Update mini-map periodically
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_minimap)
        self.update_timer.start(100)  # Update every 100 ms

        # Animation variables
        self._instruction_rect = QRectF()
        self.animation = QPropertyAnimation(self, b"instruction_rect")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setDuration(1000)  # 1 second duration
        self.animation.finished.connect(self.on_animation_finished)

        self.is_expanded = True
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.expand_instruction_rect)

        # Start the animation after a delay
        QTimer.singleShot(3000, self.start_animation)  # 3 seconds delay

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
        fm = QFontMetrics(self.instruction_font)

        # Draw background
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self._instruction_rect, 5, 5)

        # Calculate available space
        available_width = (
            self._instruction_rect.width() - 20
        )  # 10px padding on each side
        available_height = (
            self._instruction_rect.height() - 20
        )  # 10px padding on top and bottom

        # Draw text only if there's enough space
        if available_width > 100 and available_height > fm.height() * 3:
            painter.setPen(self.text_color)
            y = int(self._instruction_rect.top() + 10)
            for line in self.instruction_text.split("\n"):
                painter.drawText(int(self._instruction_rect.left() + 10), y, line)
                y += fm.height()
        else:
            # Draw an icon or symbol when the rect is small
            painter.setPen(self.icon_color)
            painter.drawText(self._instruction_rect, Qt.AlignmentFlag.AlignCenter, "?")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_minimap_and_scrollbar()
        self.viewport().update()

        # Update the instruction rectangle size
        self.update_instruction_rect()

    def update_minimap_and_scrollbar(self):
        minimap_width = 200
        minimap_height = 150
        scrollbar_height = 15
        margin = 10

        # Position zoom scrollbar
        self.zoom_scrollbar.setGeometry(
            margin,
            self.height() - minimap_height - scrollbar_height - margin,
            minimap_width,
            scrollbar_height,
        )

        # Position minimap
        self.minimap.setGeometry(
            margin,
            self.height() - minimap_height - margin,
            minimap_width,
            minimap_height,
        )
        self.minimap.show()
        self.zoom_scrollbar.show()

    def set_instruction_rect(self, rect):
        if self._instruction_rect != rect:
            self._instruction_rect = rect
            self.viewport().update()

    def get_instruction_rect(self):
        return self._instruction_rect

    instruction_rect = pyqtProperty(QRectF, get_instruction_rect, set_instruction_rect)

    def update_instruction_rect(self):
        fm = QFontMetrics(self.instruction_font)
        text_width = max(
            fm.horizontalAdvance(line) for line in self.instruction_text.split("\n")
        )
        text_height = fm.height() * len(self.instruction_text.split("\n"))
        padding = 10
        self.full_width = text_width + 2 * padding
        self.full_height = text_height + 2 * padding
        self.small_width = 30
        self.small_height = 30

        if self.is_expanded:
            self._instruction_rect = QRectF(
                padding, padding, self.full_width, self.full_height
            )
        else:
            self._instruction_rect = QRectF(
                padding, padding, self.small_width, self.small_height
            )

    def start_animation(self):
        if self.is_expanded:
            self.is_expanded = False
            self.update_instruction_rect()
            self.animation.setStartValue(
                QRectF(10, 10, self.full_width, self.full_height)
            )
            self.animation.setEndValue(
                QRectF(10, 10, self.small_width, self.small_height)
            )
            self.animation.start()

    def expand_instruction_rect(self):
        self.is_expanded = True
        self.animation.setStartValue(self._instruction_rect)
        self.animation.setEndValue(QRectF(10, 10, self.full_width, self.full_height))
        self.animation.start()

    def shrink_instruction_rect(self):
        self.is_expanded = False
        self.animation.setStartValue(self._instruction_rect)
        self.animation.setEndValue(QRectF(10, 10, self.small_width, self.small_height))
        self.animation.start()

    def on_animation_finished(self):
        self.viewport().update()

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

        # Convert QPoint to QPointF
        pos = QPointF(event.pos())

        if self._instruction_rect.contains(pos):
            if not self.is_expanded:
                self.hover_timer.start(300)  # Start expand after 300ms hover
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.hover_timer.stop()
            if self.is_expanded:
                self.shrink_instruction_rect()
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self.is_selecting:
            self.is_selecting = False
            if self.rubberBand:
                self.rubberBand.hide()
                selection_polygon = self.mapToScene(self.rubberBand.geometry())
                selection_rect = selection_polygon.boundingRect()
                self.zoom_to_rect(selection_rect)
        else:
            super().mouseReleaseEvent(event)
        self.update_minimap()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hover_timer.stop()
        if self.is_expanded:
            self.shrink_instruction_rect()

    def zoom_to_rect(self, rect):
        if not rect.isEmpty():
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.updateSceneRect(self.sceneRect().united(rect))
            self.update_zoom_factor()
            self.update_minimap()

    def update_minimap(self):
        if self.minimap.isVisible():
            self.minimap.update_minimap()

    def update_zoom_factor(self):
        current_transform = self.transform()
        current_scale = current_transform.m11()  # Horizontal scale factor
        self.current_zoom = current_scale
        self.zoomChanged.emit(current_scale)

        # Update scrollbar value
        scrollbar_value = int(
            ((self.current_zoom - self.min_zoom) / (self.max_zoom - self.min_zoom))
            * 100
        )
        self.zoom_scrollbar.setValue(scrollbar_value)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.2
            zoom_out_factor = 1 / zoom_in_factor

            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = zoom_out_factor

            resulting_zoom = self.current_zoom * zoom_factor
            if self.min_zoom <= resulting_zoom <= self.max_zoom:
                self.current_zoom = resulting_zoom
                self.zoom_to(self.current_zoom)

                # Update scrollbar value
                scrollbar_value = int(
                    (
                        (self.current_zoom - self.min_zoom)
                        / (self.max_zoom - self.min_zoom)
                    )
                    * 100
                )
                self.zoom_scrollbar.setValue(scrollbar_value)
        else:
            super().wheelEvent(event)

    def zoom_scrollbar_changed(self, value):
        zoom_factor = self.min_zoom + (value / 100) * (self.max_zoom - self.min_zoom)
        self.zoom_to(zoom_factor)

    def zoom_to(self, factor):
        self.current_zoom = factor
        self.setTransform(QTransform().scale(factor, factor))
        self.zoomChanged.emit(factor)
        self.update_minimap()
