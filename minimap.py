from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem


class MiniMap(QGraphicsView):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.setScene(QGraphicsScene(self))
        self.setFixedSize(200, 150)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "background: rgba(200, 200, 200, 150); border: 1px solid gray;"
        )
        self.viewport_rect = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def update_minimap(self):
        self.scene().clear()
        main_scene = self.main_view.scene()
        if not main_scene:
            return

        self.setSceneRect(main_scene.sceneRect())
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

        for item in main_scene.items():
            if isinstance(item, QGraphicsRectItem):
                mini_item = QGraphicsRectItem(item.rect())
                mini_item.setPos(item.scenePos())
                mini_item.setBrush(item.brush())
                mini_item.setPen(item.pen())
                self.scene().addItem(mini_item)

        viewport_rect = self.main_view.mapToScene(
            self.main_view.viewport().rect()
        ).boundingRect()
        self.viewport_rect = QGraphicsRectItem(viewport_rect)
        self.viewport_rect.setBrush(QBrush(QColor(0, 0, 255, 50)))
        self.viewport_rect.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene().addItem(self.viewport_rect)

    def mousePressEvent(self, event):
        self.pan_minimap(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.pan_minimap(event.pos())

    def pan_minimap(self, pos):
        scene_pos = self.mapToScene(pos)
        self.main_view.centerOn(scene_pos)
        self.update_minimap()
