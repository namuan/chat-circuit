from PyQt6.QtCore import (
    QObject,
    QPropertyAnimation,
    QEasingCurve,
    pyqtProperty,
    QRectF,
    Qt,
)
from PyQt6.QtGui import QPen, QBrush, QColor
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem


class CircleAnimator(QObject):
    def __init__(self):
        super().__init__()
        self._scale = 1.0

    @pyqtProperty(float)
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value


class HoverCircle(QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.normal_radius = 15
        self.hover_radius = 30
        self.setBrush(QBrush(QColor(70, 130, 180)))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setRect(-10, -10, self.normal_radius * 2, self.normal_radius * 2)

        self.animator = CircleAnimator()
        self.animation = QPropertyAnimation(self.animator, b"scale")
        self.animation.setDuration(200)
        self.animation.valueChanged.connect(self.update_scale)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.scenePos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_pos = event.scenePos() - self.drag_start_pos
            self.parentItem().moveBy(new_pos.x(), new_pos.y())
            self.drag_start_pos = event.scenePos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def update_scale(self, scale):
        center = self.rect().center()
        new_radius = self.normal_radius * scale
        new_rect = QRectF(0, 0, new_radius * 2, new_radius * 2)
        new_rect.moveCenter(center)
        self.setRect(new_rect)

    def hoverEnterEvent(self, event):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(self.hover_radius / self.normal_radius)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.start()

    def hoverLeaveEvent(self, event):
        self.animation.setStartValue(self.hover_radius / self.normal_radius)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.animation.start()
