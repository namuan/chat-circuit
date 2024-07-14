import math

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPen, QColor, QPolygonF
from PyQt6.QtWidgets import QGraphicsItemGroup, QGraphicsPolygonItem


class LinkLine(QGraphicsItemGroup):
    def __init__(self, parent, child):
        super().__init__()
        self.parent = parent
        self.child = child
        self.chevrons = []
        self.chevron_color = QColor(0, 158, 115)
        self.chevron_size = 10
        self.chevron_spacing = 30
        self.setZValue(-1)
        self.updatePosition()

    def createChevron(self, pos, angle):
        chevron = QGraphicsPolygonItem(self)
        chevron.setBrush(self.chevron_color)
        chevron.setPen(QPen(self.chevron_color, 1))

        # Create chevron points
        p1 = QPointF(-self.chevron_size / 2, -self.chevron_size / 2)
        p2 = QPointF(self.chevron_size / 2, 0)
        p3 = QPointF(-self.chevron_size / 2, self.chevron_size / 2)

        chevron.setPolygon(QPolygonF([p1, p2, p3]))
        chevron.setPos(pos)
        chevron.setRotation(math.degrees(angle))
        return chevron

    def updatePosition(self):
        parent_center = self.parent.mapToScene(self.parent.boundingRect().center())
        child_center = self.child.mapToScene(self.child.boundingRect().center())

        # Calculate the direction vector
        dx = child_center.x() - parent_center.x()
        dy = child_center.y() - parent_center.y()
        length = math.sqrt(dx ** 2 + dy ** 2)

        # Clear existing chevrons
        for chevron in self.chevrons:
            self.removeFromGroup(chevron)
        self.chevrons.clear()

        if length == 0:
            return

        # Normalize the direction vector
        dx, dy = dx / length, dy / length

        # Calculate angle for chevrons
        angle = math.atan2(dy, dx)

        # Create chevrons along the line
        num_chevrons = int(length / self.chevron_spacing)
        for i in range(num_chevrons):
            pos = QPointF(
                parent_center.x() + dx * (i + 0.5) * self.chevron_spacing,
                parent_center.y() + dy * (i + 0.5) * self.chevron_spacing
            )
            chevron = self.createChevron(pos, angle)
            self.addToGroup(chevron)
            self.chevrons.append(chevron)
