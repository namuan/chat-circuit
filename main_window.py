from PyQt6.QtWidgets import QMainWindow, QGraphicsView
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import QGraphicsScene
from command_invoker import CommandInvoker
from commands import CreateFormCommand
from form_widget import FormWidget
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal


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
        self.setWindowTitle("Form Editor")
        self.setGeometry(100, 100, 800, 600)

        self.scene = GraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        # Add Undo and Redo actions
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)

        # Add actions to menu
        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(undo_action)
        edit_menu.addAction(redo_action)

    def undo(self):
        self.scene.command_invoker.undo()

    def redo(self):
        self.scene.command_invoker.redo()
