import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import QGraphicsScene, QFileDialog
from PyQt6.QtWidgets import QMainWindow, QGraphicsView

from command_invoker import CommandInvoker
from commands import CreateFormCommand
from form_widget import FormWidget


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_invoker = CommandInvoker()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Create a new form when left-click + Cmd/Ctrl is pressed
            command = CreateFormCommand(self)
            self.command_invoker.execute(command)
            new_form = command.created_form
            new_form.setPos(event.scenePos())
        else:
            super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Circuit")
        self.setGeometry(100, 100, 800, 600)

        self.scene = GraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.create_menu()

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

    def save_state(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json)")
        state = []
        for item in self.scene.items():
            if isinstance(item, FormWidget) and not item.parent_form:
                state.append(item.to_dict())

        with open(file_name, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")
        if os.path.exists(file_name):
            with open(file_name, 'r') as f:
                state = json.load(f)

            self.scene.clear()
            for form_data in state:
                FormWidget.from_dict(form_data, self.scene)
        else:
            print(f"File {file_name} not found.")

    def undo(self):
        self.scene.command_invoker.undo()

    def redo(self):
        self.scene.command_invoker.redo()
