import json
import os

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction, QKeySequence, QTransform, QPainter
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QMessageBox,
)

from command_invoker import CommandInvoker
from commands import CreateFormCommand
from form_widget import FormWidget
from state_manager import StateManager


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_invoker = CommandInvoker()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            # Create a new form when left-click + Cmd/Ctrl is pressed
            command = CreateFormCommand(self)
            self.command_invoker.execute(command)
            new_form = command.created_form
            new_form.setPos(event.scenePos())
        else:
            super().mousePressEvent(event)


class PanningGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._pan_start = QPoint()
        self._is_panning = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_start = event.position().toPoint()
            self._is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.position().toPoint() - self._pan_start
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            self._pan_start = event.position().toPoint()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


APPLICATION_TITLE = "Chat Circuit"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state_manager = StateManager("deskriders", "chatcircuit")
        self.setWindowTitle(APPLICATION_TITLE)

        self.scene = GraphicsScene()
        self.view = PanningGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.zoom_factor = 1.0
        self.create_menu()
        self.restoreApplicationState()

    def create_menu(self):
        # File menu
        file_menu = self.menuBar().addMenu("File")

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_state)
        file_menu.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        load_action.triggered.connect(self.load_state)
        file_menu.addAction(load_action)

        # Edit menu
        edit_menu = self.menuBar().addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        # View menu
        view_menu = self.menuBar().addMenu("View")

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

    def save_state(self):
        file_name = self.state_manager.get_last_file()
        if not file_name:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "JSON Files (*.json)"
            )

        state = []
        for item in self.scene.items():
            if isinstance(item, FormWidget) and not item.parent_form:
                state.append(item.to_dict())

        with open(file_name, "w") as f:
            json.dump(state, f, indent=2)

        self.setWindowTitle(f"{APPLICATION_TITLE} - {file_name}")
        self.state_manager.save_last_file(file_name)

    def load_state(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "JSON Files (*.json)"
        )
        if os.path.exists(file_name):
            self.load_from_file(file_name)
        else:
            print(f"File {file_name} not found.")

    def load_from_file(self, file_name):
        if os.path.exists(file_name):
            with open(file_name) as f:
                state = json.load(f)

        self.scene.clear()
        for form_data in state:
            FormWidget.from_dict(form_data, self.scene)
        self.setWindowTitle(f"{APPLICATION_TITLE} - {file_name}")

    def undo(self):
        self.scene.command_invoker.undo()

    def redo(self):
        self.scene.command_invoker.redo()

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_zoom()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_zoom()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_zoom()

    def update_zoom(self):
        transform = QTransform()
        transform.scale(self.zoom_factor, self.zoom_factor)
        self.view.setTransform(transform)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def restoreApplicationState(self):
        if not self.state_manager.restore_window_state(self):
            self.showMaximized()

        file_name = self.state_manager.get_last_file()
        if file_name and isinstance(file_name, str):
            self.load_from_file(file_name)
        else:
            QMessageBox.warning(
                self, "Error", f"Failed to load the last file: {file_name}"
            )

    def closeEvent(self, event):
        self.state_manager.save_window_state(self)
        self.save_state()
        super().closeEvent(event)
