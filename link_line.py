from PyQt6.QtWidgets import QGraphicsLineItem
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen, QColor


class LinkLine(QGraphicsLineItem):
    def __init__(self, parent, child):
        super().__init__()
        self.parent = parent
        self.child = child
        self.setPen(QPen(QColor(100, 100, 100), 2, Qt.PenStyle.DashLine))
        self.setZValue(-1)  # Ensure the line is drawn behind the forms
        self.updatePosition()

    def updatePosition(self):
        parent_center = self.parent.mapToScene(self.parent.boundingRect().center())
        child_center = self.child.mapToScene(self.child.boundingRect().center())
        self.setLine(parent_center.x(), parent_center.y(), child_center.x(), child_center.y())
