import faulthandler
import json
import logging
import logging.handlers
import math
import os
import platform
import random
import re
import sys
import uuid
from abc import ABC, abstractmethod
from collections import deque
from os import linesep
from pathlib import Path

import keyring
import mistune
import requests
from duckduckgo_search import DDGS
from litellm import completion
from PyQt6.QtCore import (
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    QRunnable,
    QSettings,
    QSize,
    QSizeF,
    Qt,
    QThreadPool,
    QTimer,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QIcon,
    QImage,
    QKeyEvent,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QTextDocument,
    QTransform,
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsItemGroup,
    QGraphicsLinearLayout,
    QGraphicsPolygonItem,
    QGraphicsProxyWidget,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRubberBand,
    QScrollBar,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# Logging Configuration
class ChatCircuitLogger:
    """Centralized logging configuration for ChatCircuit application."""

    def __init__(self, app_name: str = "ChatCircuit"):
        self.app_name = app_name
        self.log_dir = self._get_log_directory()
        self.logger = None
        self._setup_logging()

    def _get_log_directory(self) -> Path:
        """Get OS-specific log directory."""
        system = platform.system().lower()

        if system == "darwin":  # macOS
            log_dir = Path.home() / "Library" / "Logs" / self.app_name
        elif system == "windows":
            appdata = os.getenv("APPDATA")
            if appdata:
                log_dir = Path(appdata) / self.app_name / "logs"
            else:
                log_dir = Path.home() / "AppData" / "Roaming" / self.app_name / "logs"
        else:  # Linux and other Unix-like systems
            log_dir = Path.home() / ".local" / "share" / self.app_name / "logs"

        # Create directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _setup_logging(self) -> None:
        """Set up logging configuration with rotating file handlers."""
        # Create main logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if logger already configured
        if self.logger.handlers:
            return

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        simple_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")

        # File handler for all logs (rotating)
        main_log_file = self.log_dir / "chatcircuit.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Error-only file handler
        error_log_file = self.log_dir / "chatcircuit_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)

        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

        # Log initial setup
        self.logger.info("Logging initialized for %s", self.app_name)
        self.logger.info("Log directory: %s", self.log_dir)
        self.logger.info("Platform: %s %s", platform.system(), platform.release())

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Get a logger instance."""
        if name:
            return logging.getLogger(f"{self.app_name}.{name}")
        return self.logger

    def get_log_directory(self) -> Path:
        """Get the log directory path."""
        return self.log_dir


# Global logger instance
_chat_circuit_logger = None


def setup_logging(app_name: str = "ChatCircuit") -> ChatCircuitLogger:
    """Set up global logging configuration."""
    global _chat_circuit_logger
    if _chat_circuit_logger is None:
        _chat_circuit_logger = ChatCircuitLogger(app_name)
    return _chat_circuit_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance."""
    if _chat_circuit_logger is None:
        setup_logging()
    return _chat_circuit_logger.get_logger(name)


def get_log_directory() -> Path:
    """Get the log directory path."""
    if _chat_circuit_logger is None:
        setup_logging()
    return _chat_circuit_logger.get_log_directory()


faulthandler.enable()
with Path("crash.log").open("w") as f:
    faulthandler.dump_traceback(f)

# Initialize logging system
setup_logging("ChatCircuit")
logger = get_logger("main")

APPLICATION_TITLE = "Chat Circuit"


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path().resolve()

    return base_path / relative_path


def load_models_from_config(config_file="models.conf"):
    config_logger = get_logger("config")
    config_path = Path(__file__).parent / config_file

    try:
        with config_path.open() as f:
            models = [line.strip() for line in f if line.strip()]
        config_logger.info("Loaded %s models from %s", len(models), config_file)
    except FileNotFoundError:
        config_logger.warning("Config file %s not found. Using default models.", config_file)
        models = [
            "llama3:latest",
            "mistral:latest",
            "tinyllama:latest",
        ]

    return models


LLM_MODELS = load_models_from_config()
DEFAULT_LLM_MODEL = LLM_MODELS[0]

thread_pool = QThreadPool()
active_workers = 0


class DuckDuckGo:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str) -> str:
        results = self.ddgs.text(query, max_results=10)
        processed_results = [
            f"**[{result['title']}]({result['href']})**\n\n{result['body']}\n\n{result['href']}" for result in results
        ]
        return "### Search Results\n\n" + "\n\n".join(processed_results)


class CustomFilePicker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        button_style = """
            background-color: #F0F0F0;
            text-align: center;
            border: 1px solid #808080;
            font-size: 18px;
        """

        self.selected_file_paths = []
        self.file_count_button = QPushButton("0")
        self.file_count_button.setFixedSize(28, 26)
        self.file_count_button.setStyleSheet(button_style + "border-right: none;")
        self.file_count_button.clicked.connect(self.show_file_list)

        self.attach_file_button = QPushButton()
        self.attach_file_button.setIcon(QIcon.fromTheme("mail-attachment"))
        self.attach_file_button.setStyleSheet(button_style + "border-left: none;")
        self.attach_file_button.clicked.connect(self.open_file_dialog)
        self.attach_file_button.setFixedSize(28, 26)

        main_layout.addWidget(self.file_count_button)
        main_layout.addWidget(self.attach_file_button)

        self.setLayout(main_layout)

    def get_selected_files(self):
        return self.selected_file_paths

    def set_selected_files(self, files):
        self.selected_file_paths = files
        self.update_file_count()

    def update_file_count(self):
        self.file_count_button.setText(str(len(self.selected_file_paths)))

    def open_file_dialog(self):
        file_dialog = QFileDialog(None)
        file_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        file_dialog.setWindowTitle("Select a File")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            if selected_file not in self.selected_file_paths:
                self.selected_file_paths.append(selected_file)
                self.update_file_count()

    def show_file_list(self):
        if self.selected_file_paths:
            file_list_dialog = QDialog(None)
            file_list_dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)

            dialog_layout = QVBoxLayout(file_list_dialog)
            dialog_layout.setContentsMargins(0, 0, 0, 0)
            dialog_layout.setSpacing(0)

            file_list_widget = QListWidget()
            file_list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                outline: none;
                background-color: white;
            }
            QListWidget::item {
                border: none;
                padding: 0;
                height: 30px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
            """)

            for file_path in self.selected_file_paths:
                file_name = Path(file_path).name
                file_item_widget = QWidget()
                file_item_layout = QHBoxLayout(file_item_widget)
                file_item_layout.setContentsMargins(5, 0, 5, 0)
                file_item_layout.setSpacing(5)

                remove_file_button = QPushButton("x")
                remove_file_button.setFixedSize(20, 20)
                remove_file_button.setStyleSheet("""
                QPushButton {
                    border: none;
                    background-color: transparent;
                    color: red;
                    font-weight: bold;
                    font-size: 18px;
                }
                QPushButton:hover {
                    color: darkred;
                }
                """)
                remove_file_button.clicked.connect(lambda _, path=file_path: self.remove_file(path, file_list_widget))

                file_name_label = QLabel(file_name)
                file_name_label.setStyleSheet("""
                color: #333;
                background: transparent;
                border: none;
                font-size: 13px;
                """)

                file_item_layout.addWidget(remove_file_button)
                file_item_layout.addWidget(file_name_label, 1)

                file_list_item = QListWidgetItem(file_list_widget)
                file_list_widget.addItem(file_list_item)
                file_list_widget.setItemWidget(file_list_item, file_item_widget)

            dialog_layout.addWidget(file_list_widget)
            file_list_dialog.setLayout(dialog_layout)

            item_height = 30  # This should match the height in the CSS
            num_items = len(self.selected_file_paths)
            calculated_height = num_items * item_height

            max_height = 300
            dialog_height = min(calculated_height, max_height)

            # Set the fixed width and calculated height
            file_list_dialog.setFixedSize(300, dialog_height)

            self.dialog = file_list_dialog
            self.update_list_position(calculated_height)

            class ClickOutsideFilter(QObject):
                def __init__(self, dialog):
                    super().__init__()
                    self.dialog = dialog

                def eventFilter(self, obj, event):
                    if (
                        event.type() == QEvent.Type.Leave
                        and obj == self.dialog
                        and not self.dialog.geometry().contains(QCursor.pos())
                    ):
                        self.dialog.close()
                        return True
                    return False

            click_outside_filter = ClickOutsideFilter(file_list_dialog)
            file_list_dialog.installEventFilter(click_outside_filter)

            file_list_dialog.activateWindow()
            file_list_dialog.raise_()
            file_list_dialog.exec()

            file_list_dialog.removeEventFilter(click_outside_filter)

    def remove_file(self, file_path, file_list_widget):
        if file_path in self.selected_file_paths:
            index = self.selected_file_paths.index(file_path)
            del self.selected_file_paths[index]
            self.update_file_count()
            file_list_widget.takeItem(index)

    def update_list_position(self, list_height: int):
        file_count_button_pos = self.file_count_button.mapToGlobal(self.file_count_button.rect().topLeft())
        self.dialog.move(file_count_button_pos.x(), file_count_button_pos.y() - list_height)


class CommandInvoker:
    def __init__(self):
        self.history = []
        self.redo_stack = []

    def execute(self, command):
        command.execute()
        self.history.append(command)
        self.redo_stack.clear()

    def undo(self):
        if self.history:
            command = self.history.pop()
            command.undo()
            self.redo_stack.append(command)

    def redo(self):
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.history.append(command)


def _validate_svg_file(file_path):
    """Validate that the file exists and appears to be a valid SVG."""
    path_obj = Path(file_path)
    if not path_obj.exists():
        logger.warning("SVG icon file not found: %s", file_path)
        return False

    # Check file size
    file_size = path_obj.stat().st_size
    logger.debug("SVG file size: %s bytes", file_size)

    if file_size == 0:
        logger.warning("SVG icon file is empty: %s", file_path)
        return False

    # Try to validate SVG content
    try:
        with Path(file_path).open(encoding="utf-8") as f:
            content = f.read()
            if not content.strip().startswith("<svg"):
                logger.warning("File does not appear to be a valid SVG: %s", file_path)
                return False
    except Exception as read_error:
        logger.warning("Could not read SVG file %s: %s", file_path, read_error)
        return False

    return True


def _create_icon_with_renderer(file_path):
    """Create a QIcon using QSvgRenderer."""
    try:
        renderer = QSvgRenderer(str(file_path))
        if renderer.isValid():
            # Create a pixmap from the SVG
            size = renderer.defaultSize()
            if size.width() > 0 and size.height() > 0:
                pixmap = QPixmap(size)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()

                icon = QIcon(pixmap)
                if not icon.isNull():
                    logger.debug("Successfully created SVG icon using QSvgRenderer: %s", file_path)
                    return icon
                logger.warning("QIcon created from pixmap is null: %s", file_path)
            else:
                logger.warning("SVG has invalid size %dx%d: %s", size.width(), size.height(), file_path)
        else:
            logger.warning("QSvgRenderer reports invalid SVG: %s", file_path)
    except Exception as svg_error:
        logger.warning("QSvgRenderer failed for %s: %s", file_path, svg_error)

    return None


def _create_icon_directly(file_path):
    """Create a QIcon by direct loading."""
    try:
        icon = QIcon(str(file_path))
        if not icon.isNull():
            logger.debug("Successfully created icon using direct QIcon: %s", file_path)
            return icon
        logger.warning("Direct QIcon loading failed (icon is null): %s", file_path)
    except Exception as icon_error:
        logger.warning("Direct QIcon loading failed with exception: %s: %s", file_path, icon_error)

    return None


def create_svg_icon(file_path):
    """Create a QIcon from an SVG file path with enhanced error handling."""
    logger.debug("Attempting to create SVG icon from: %s", file_path)

    try:
        # First validate the file
        if not _validate_svg_file(file_path):
            return QIcon()

        # Try QSvgRenderer first for better SVG support
        icon = _create_icon_with_renderer(file_path)
        if icon:
            return icon

        # Fallback to direct QIcon loading
        icon = _create_icon_directly(file_path)
        if icon:
            return icon

    except Exception:
        logger.exception("Unexpected error creating SVG icon from %s")

    # Return an empty icon as fallback
    logger.warning("All SVG icon loading methods failed for: %s", file_path)
    return QIcon()


def create_button(icon_path, tooltip, callback):
    button_widget = QGraphicsProxyWidget()
    button = QPushButton()
    button.setStyleSheet(
        """
        QPushButton {
            border: 1px solid #808080;
        }
    """
    )
    icon = create_svg_icon(icon_path)
    button.setIcon(icon)
    button.setIconSize(QSize(24, 24))
    button.setToolTip(tooltip)
    button.clicked.connect(callback)
    button_widget.setWidget(button)
    return button_widget


def add_buttons(form_widget, picker):
    bottom_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)

    # Define button configurations
    buttons = [
        (resource_path("resources/ripple.svg"), "Re-Run", form_widget.re_run_all),
        (resource_path("resources/fork.svg"), "Fork", form_widget.clone_form),
        (
            resource_path("resources/clone.svg"),
            "Clone Branch",
            form_widget.clone_branch,
        ),
        (
            resource_path("resources/bulb.svg"),
            "Follow-up Questions",
            form_widget.generate_follow_up_questions,
        ),
        (resource_path("resources/delete.svg"), "Delete", form_widget.delete_form),
    ]

    picker_widget = QGraphicsProxyWidget()
    picker_widget.setWidget(picker)
    bottom_layout.addItem(picker_widget)

    # Create and add buttons
    for icon_path, tooltip, callback in buttons:
        button_widget = create_button(icon_path, tooltip, callback)
        bottom_layout.addItem(button_widget)

    return bottom_layout


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass


class CreateFormCommand(Command):
    def __init__(self, scene, parent_form=None, position=None, model=DEFAULT_LLM_MODEL):
        self.scene = scene
        self.parent_form = parent_form
        self.model = model
        self.created_form = None
        self.position = position
        self.link_line = None

    def execute(self):
        self.created_form = FormWidget(parent=self.parent_form, model=self.model)
        self.scene.addItem(self.created_form)
        if self.position:
            self.created_form.setPos(self.position)
        if self.parent_form:
            self.parent_form.child_forms.append(self.created_form)
            self.link_line = LinkLine(self.parent_form, self.created_form)
            self.scene.addItem(self.link_line)
            self.created_form.link_line = self.link_line

    def undo(self):
        if self.created_form:
            if self.created_form.scene() == self.scene:
                self.scene.removeItem(self.created_form)
            if self.parent_form and self.created_form in self.parent_form.child_forms:
                self.parent_form.child_forms.remove(self.created_form)
            if self.link_line and self.link_line.scene() == self.scene:
                self.scene.removeItem(self.link_line)
            self.created_form = None
            self.link_line = None


class DeleteFormCommand(Command):
    def __init__(self, form):
        self.form = form
        self.parent_form = form.parent_form
        self.child_forms = form.child_forms[:]
        self.link_line = form.link_line
        self.scene = form.scene()
        self.pos = form.pos()
        self.deleted_subtree = []

    def execute(self):
        self.deleted_subtree = self._delete_subtree(self.form)
        if self.parent_form and self.form in self.parent_form.child_forms:
            self.parent_form.child_forms.remove(self.form)

    def undo(self):
        self._restore_subtree(self.deleted_subtree)
        if self.parent_form:
            self.parent_form.child_forms.append(self.form)

    def _delete_subtree(self, form):
        deleted = []
        for child in form.child_forms[:]:
            deleted.extend(self._delete_subtree(child))

        if form.scene() == self.scene:
            self.scene.removeItem(form)
        if form.link_line and form.link_line.scene() == self.scene:
            self.scene.removeItem(form.link_line)

        deleted.append((form, form.pos(), form.link_line))
        return deleted

    def _restore_subtree(self, deleted_items):
        for form, pos, link_line in reversed(deleted_items):
            self.scene.addItem(form)
            form.setPos(pos)
            if link_line:
                self.scene.addItem(link_line)
                form.link_line = link_line


class MoveFormCommand(Command):
    def __init__(self, form, old_pos, new_pos):
        self.form = form
        self.old_pos = old_pos
        self.new_pos = new_pos

    def execute(self):
        self.form.setPos(self.new_pos)
        if self.form.link_line:
            self.form.link_line.update_position()

    def undo(self):
        self.form.setPos(self.old_pos)
        if self.form.link_line:
            self.form.link_line.update_position()


class CloneBranchCommand(Command):
    def __init__(self, scene, source_form):
        self.scene = scene
        self.source_form = source_form
        self.cloned_forms = []
        self.parent_form = None

    def execute(self):
        self.parent_form = self.source_form.parent_form
        new_pos = self.source_form.pos() + QPointF(200, 600)  # Offset the new branch
        self.cloned_forms = self._clone_branch(self.source_form, self.parent_form, new_pos)

    def undo(self):
        for form in self.cloned_forms:
            if form.scene() == self.scene:
                self.scene.removeItem(form)
            if form.link_line and form.link_line.scene() == self.scene:
                self.scene.removeItem(form.link_line)
        if self.parent_form:
            self.parent_form.child_forms = [f for f in self.parent_form.child_forms if f not in self.cloned_forms]

    def _clone_branch(self, source_form, parent_form, position):
        cloned_form = FormWidget(parent=parent_form, model=source_form.model)
        cloned_form.setPos(position)
        cloned_form.input_box.widget().setPlainText(source_form.input_box.widget().toPlainText())
        cloned_form.conversation_area.widget().setPlainText(source_form.conversation_area.widget().toPlainText())

        self.scene.addItem(cloned_form)

        if parent_form:
            parent_form.child_forms.append(cloned_form)
            link_line = LinkLine(parent_form, cloned_form)
            self.scene.addItem(link_line)
            cloned_form.link_line = link_line

        cloned_forms = [cloned_form]

        for child in source_form.child_forms:
            child_pos = cloned_form.pos() + (child.pos() - source_form.pos())
            cloned_forms.extend(self._clone_branch(child, cloned_form, child_pos))

        return cloned_forms


class HeaderWidget(QGraphicsWidget):
    model_changed = pyqtSignal(str)

    def __init__(self, model_name):
        super().__init__()

        self.model_dropdown = QComboBox()
        self.progress_bar = QProgressBar()
        self.model_name = model_name
        self.is_initialized = False

        self.setMinimumHeight(30)  # Reduced height
        self.setMaximumHeight(30)

        QTimer.singleShot(0, self.create_widgets)

    def create_widgets(self):
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.model_dropdown.addItems(LLM_MODELS)
        self.model_dropdown.setStyleSheet(
            """
            QComboBox {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 3px;
                padding: 5px 25px 5px 5px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #34495e;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: none;  /* Remove default arrow image */
                width: 10px;
                height: 15px;
                margin-right: 5px;
            }
            QComboBox::down-arrow:on {
                top: 1px;
                left: 1px;
            }
            QComboBox::down-arrow::after {
                content: "";
                display: block;
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ecf0f1;  /* Arrow color */
            }
            QComboBox QAbstractItemView {
                background-color: #34495e;
                color: #ecf0f1;
                selection-background-color: #3498db;
            }
            """
        )
        self.model_dropdown.currentTextChanged.connect(self.on_model_changed)

        main_layout.addWidget(self.model_dropdown)

        self.progress_bar.setRange(0, 0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #ecf0f1;
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 1px;
            }
            """
        )
        self.progress_bar.hide()

        main_layout.addWidget(self.progress_bar)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(container)

        layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addItem(proxy)
        self.setLayout(layout)

        self.is_initialized = True
        self.update_model_name()

    def start_processing(self):
        if self.is_initialized and self.progress_bar:
            self.progress_bar.show()

    def stop_processing(self):
        if self.is_initialized and self.progress_bar:
            self.progress_bar.hide()

    def on_model_changed(self, new_model):
        self.model_name = new_model
        self.model_changed.emit(new_model)

    def update_model_name(self):
        if self.is_initialized and self.model_dropdown:
            self.model_dropdown.setCurrentText(self.model_name)


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
        self.normal_radius = 10
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
        self.update_position()

    def create_chevron(self, pos, angle):
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

    def update_position(self):
        parent_center = self.parent.mapToScene(self.parent.boundingRect().center())
        child_center = self.child.mapToScene(self.child.boundingRect().center())

        # Calculate the direction vector
        dx = child_center.x() - parent_center.x()
        dy = child_center.y() - parent_center.y()
        length = math.sqrt(dx**2 + dy**2)

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
                parent_center.y() + dy * (i + 0.5) * self.chevron_spacing,
            )
            chevron = self.create_chevron(pos, angle)
            self.addToGroup(chevron)
            self.chevrons.append(chevron)


class HtmlRenderer(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__()
        self.text_document = QTextDocument()

    def render(self, text):
        markdown = mistune.create_markdown(renderer=self)
        html = markdown(text)
        self.text_document.setHtml(html)
        return self.text_document


class LlmWorkerSignals(QObject):
    update = pyqtSignal(str)
    finished = pyqtSignal()
    notify_child = pyqtSignal()
    error = pyqtSignal(str)


class LlmWorker(QRunnable):
    def __init__(self, model, system_message, messages):
        super().__init__()
        self.model = model
        self.messages = messages
        self.system_message = system_message or "You are a helpful assistant."
        self.signals = LlmWorkerSignals()
        self.logger = get_logger("llm_worker")

    def run(self):
        self.logger.info("Starting LLM worker execution with model: %s", self.model)
        self.logger.debug("Processing %s messages", len(self.messages))

        try:
            formatted_messages = []
            if self.system_message:
                formatted_messages.append({"role": "system", "content": self.system_message})
            formatted_messages.extend(self.messages)

            self.logger.debug("Formatted %s messages for LLM", len(formatted_messages))

            response = completion(
                model=f"{self.model}",
                messages=formatted_messages,
                api_base="http://localhost:11434",
            )

            content = response.choices[0].message.content
            self.logger.info("LLM response received: %s characters", len(content))
            self.signals.update.emit(content)
            self.signals.finished.emit()

        except Exception as e:
            self.logger.exception("LLM worker error with model %s")
            self.signals.error.emit(str(e))
        finally:
            self.logger.debug("LLM worker execution completed")
            self.signals.notify_child.emit()


class SearchWorkerSignals(QObject):
    result = pyqtSignal(str)
    error = pyqtSignal(str)


class SearchWorker(QRunnable):
    def __init__(self, query):
        super().__init__()
        self.search_engine = DuckDuckGo()
        self.query = query
        self.signals = SearchWorkerSignals()
        self.logger = get_logger("search_worker")

    def run(self):
        self.logger.info(
            "Starting search worker execution for query: '%s%s'", self.query[:50], "..." if len(self.query) > 50 else ""
        )
        self.logger.debug("Full search query: %s", self.query)

        try:
            search_results = self.search_engine.search(self.query)
            self.logger.info("Search completed successfully: %s characters returned", len(search_results))
            self.signals.result.emit(search_results)
        except Exception as e:
            self.logger.exception("Search worker error for query '%s...'")
            self.signals.error.emit(str(e))
        finally:
            self.logger.debug("Search worker execution completed")


class JinaReaderWorkerSignals(QObject):
    result = pyqtSignal(str)
    error = pyqtSignal(str)


class JinaReaderWorker(QRunnable):
    def __init__(self, url, jina_api_key):
        super().__init__()
        self.url = url
        self.jina_api_key = jina_api_key
        self.signals = JinaReaderWorkerSignals()

    def run(self):
        try:
            jina_url = f"https://r.jina.ai/{self.url}"
            headers = {
                "Authorization": f"Bearer {self.jina_api_key}",
                "x-engine": "readerlm-v2",
            }
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()

            content = response.text
            self.signals.result.emit(content)
        except Exception as e:
            self.signals.error.emit(str(e))


class ResizeHandle(QGraphicsWidget):
    resize_signal = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, False)
        self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        self.setZValue(2)
        self.setGeometry(QRectF(0, 0, 10, 10))
        self.initial_pos = QPointF()
        self.initial_size = QSizeF()
        self.resizing = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = True
            self.initial_pos = event.scenePos()
            parent = self.parentItem()
            if isinstance(parent, FormWidget):
                self.initial_size = parent.size()
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.resizing:
            delta = event.scenePos() - self.initial_pos
            new_width = max(self.initial_size.width() + delta.x(), self.parentItem().minimumWidth())
            new_height = max(
                self.initial_size.height() + delta.y(),
                self.parentItem().minimumHeight(),
            )
            self.resize_signal.emit(QPointF(new_width, new_height))
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        if self.resizing:
            self.resizing = False
            event.accept()
        else:
            event.ignore()

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(QColor(Qt.GlobalColor.darkGray).lighter(128)))
        painter.setPen(QPen(Qt.GlobalColor.darkGray, 2))
        painter.drawRect(self.boundingRect())


class FormWidget(QGraphicsWidget):
    def __init__(self, parent=None, model=None):
        super().__init__()
        # LLM
        self.model = model
        self.system_message = "You are a helpful assistant."

        # Initialize logger for this form
        self.logger = get_logger("form")

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.parent_form = parent
        self.child_forms = []
        self.link_line = None

        # Re-Run all form nodes
        self.llm_worker = None
        self.jina_worker = None
        self.form_chain = deque()

        # Create main layout
        self.main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Create and add header
        self.header = HeaderWidget(self.model)
        self.header.model_changed.connect(self.on_model_changed)
        self.header.setZValue(1)
        self.main_layout.addItem(self.header)
        self.header.update_model_name()

        # Create chat layout
        chat_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Conversation area
        self.markdown_content = ""
        self.custom_font = QFont("Fantasque Sans Mono", 18)
        self.conversation_area = QGraphicsProxyWidget()
        conversation_widget = QTextBrowser()
        conversation_widget.setReadOnly(True)
        conversation_widget.setAcceptRichText(True)
        conversation_widget.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: white;
                border: 1px solid #ccc;
                font-family: {self.custom_font.family()};
                font-size: {self.custom_font.pointSize()}pt;
            }}
            QTextBrowser a {{
                color: #0066cc;
                text-decoration: none;
            }}
            QTextBrowser a:hover {{
                text-decoration: underline;
                cursor: pointer;
            }}
            """
        )
        conversation_widget.setOpenExternalLinks(False)
        conversation_widget.setOpenLinks(False)
        conversation_widget.anchorClicked.connect(self.handle_link_click)
        self.conversation_area.setWidget(conversation_widget)
        chat_layout.addItem(self.conversation_area)
        self.conversation_area.widget().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conversation_area.widget().customContextMenuRequested.connect(self.show_context_menu)

        # Create a horizontal layout for emoji and input box
        input_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)

        # Input box
        self.input_box = QGraphicsProxyWidget()
        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText("Prompt (and press Ctrl+Enter to submit)")
        self.input_text_edit.setMinimumHeight(30)
        self.input_text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.input_box.setWidget(self.input_text_edit)
        self.input_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Connect the key press event
        self.input_text_edit.installEventFilter(self)

        input_layout.addItem(self.input_box)

        # Create labels
        self.web_emoji_label = self.create_emoji_label(emoji="🌐", click_handler=self.web_emoji_label_clicked)
        self.emoji_label = self.create_emoji_label(emoji="❓", click_handler=self.emoji_label_clicked)
        self.emoji_container = QWidget()
        emoji_container_layout = QHBoxLayout(self.emoji_container)
        emoji_container_layout.setSpacing(2)
        emoji_container_layout.addWidget(self.web_emoji_label)
        emoji_container_layout.addWidget(self.emoji_label)
        emoji_container_layout.setContentsMargins(0, 0, 0, 0)
        self.emoji_proxy = QGraphicsProxyWidget()
        self.emoji_proxy.setWidget(self.emoji_container)
        input_layout.addItem(self.emoji_proxy)

        QTimer.singleShot(0, self.adjust_input_box_height)

        chat_layout.addItem(input_layout)

        # Add form layout to main layout
        self.main_layout.addItem(chat_layout)

        # Create bottom buttons layout
        self.picker = CustomFilePicker()
        self.picker.setFixedSize(56, 26)
        bottom_layout = add_buttons(self, self.picker)

        # Add bottom layout to main layout
        self.main_layout.addItem(bottom_layout)

        # Set the layout for this widget
        QTimer.singleShot(0, self.set_focus_to_input)

        self.background_item = QGraphicsRectItem(self.boundingRect(), self)
        self.background_item.setBrush(QBrush(QColor(240, 240, 240)))
        self.background_item.setZValue(-1)  # Ensure it's behind other items

        self.highlight_color = QColor(255, 165, 0, 150)  # Orange with alpha 150
        self.original_color = QColor(240, 240, 240)  # Light gray

        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.timeout.connect(self.remove_highlight)

        self.setLayout(self.main_layout)

        self.resize_handle = ResizeHandle(self)
        self.resize_handle.resize_signal.connect(self.resize_widget)
        self.update_resize_handle()

        self.circle_item = HoverCircle(self)
        self.circle_item.setZValue(2)

        self.animation = QPropertyAnimation(self, b"geometry")  # NEW: Create animation
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def to_markdown(self):
        """Convert form content to markdown format."""
        markdown = []

        # Add prompt
        prompt = self.input_box.widget().toPlainText().strip()
        if prompt:
            markdown.append("## ❓")
            markdown.append(prompt + "\n")

        # Add response
        response = self.conversation_area.widget().toPlainText().strip()
        if response:
            markdown.append("## 🤖")
            markdown.append(response + "\n")

        # Add model info
        if self.model:
            markdown.append(f"*⚙️: {self.model}*\n")

        return "\n".join(markdown)

    def get_markdown_hierarchy(self, level=1):
        """Get markdown content for this form and all its children."""
        markdown = [self.to_markdown()]

        # Add children content
        for child in self.child_forms:
            markdown.append(child.get_markdown_hierarchy(level + 1))

        return "\n".join(markdown)

    def show_context_menu(self, position):
        context_menu = QMenu()
        create_new_form_action = QAction("Explain this ...", self)
        create_new_form_action.triggered.connect(self.create_new_form_from_selection)
        context_menu.addAction(create_new_form_action)

        # Show the context menu
        context_menu.exec(self.conversation_area.widget().mapToGlobal(position))

    def create_new_form_from_selection(self):
        selected_text = self.conversation_area.widget().textCursor().selectedText()
        if selected_text:
            self.logger.info(
                "Creating new form from selection: '%s%s'", selected_text[:50], "..." if len(selected_text) > 50 else ""
            )
            self.logger.debug("Selected text length: %s characters", len(selected_text))

            try:
                # Get the scene and create a new position for the new form
                scene = self.scene()
                new_pos = self.pos() + QPointF(500, 200)  # Offset from current form
                self.logger.debug("New form position: (%.1f, %.1f)", new_pos.x(), new_pos.y())

                # Create a new form using the existing CreateFormCommand
                command = CreateFormCommand(scene, self, new_pos, self.model)
                scene.command_invoker.execute(command)
                new_form = command.created_form
                new_form.input_box.widget().setPlainText(f"Explain {selected_text}")
                self.logger.info("New form created successfully from selection")
            except Exception:
                self.logger.exception("Failed to create form from selection: %s")
                raise
        else:
            self.logger.debug("No text selected for form creation")

    def expand_form(self):
        text_edit = self.conversation_area.widget()
        doc = text_edit.document()
        text_height = doc.size().height() + 100  # Add some padding

        new_height = max(
            text_height + self.input_box.size().height() + self.header.size().height() + 50,
            self.minimumHeight(),
        )

        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRectF(self.pos(), QSizeF(self.size().width(), new_height)))
        self.animation.start()

    def create_emoji_label(self, emoji, click_handler, font_size=14, hover_color="lightgray"):
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: {font_size}px;
            }}
            QLabel:hover {{
                background-color: {hover_color};
            }}
        """
        )
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setCursor(Qt.CursorShape.PointingHandCursor)
        emoji_label.mousePressEvent = click_handler
        return emoji_label

    def emoji_label_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.submit_form()

    def web_emoji_label_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.submit_search()

    def resize_widget(self, new_size: QPointF):
        new_width = max(new_size.x(), self.minimumWidth())
        new_height = max(new_size.y(), self.minimumHeight())
        self.prepareGeometryChange()
        self.resize(new_width, new_height)
        self.update_resize_handle()

    def update_resize_handle(self):
        if self.resize_handle:
            self.resize_handle.setPos(self.rect().width() - 10, self.rect().height() - 10)

    def eventFilter(self, obj, event):
        if (
            obj == self.input_text_edit
            and event.type() == event.Type.KeyPress
            and event.key() == Qt.Key.Key_Return
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.submit_form()
            return True
        return super().eventFilter(obj, event)

    def adjust_input_box_height(self):
        document = self.input_text_edit.document()
        new_height = max(document.size().height() + 10, 30)  # Add some padding and set minimum height
        if new_height != self.input_box.size().height():
            max_height = 150
            new_height = min(int(new_height), max_height)
            self.input_box.setMinimumHeight(new_height)
            self.input_box.setMaximumHeight(new_height)

            # Adjust emoji container height
            self.emoji_container.setFixedHeight(new_height)

            self.layout().invalidate()
            QTimer.singleShot(0, self.updateGeometry)

    def highlight(self):
        self.background_item.setBrush(QBrush(self.highlight_color))
        self.highlight_timer.start(1000)

    def remove_highlight(self):
        self.background_item.setBrush(QBrush(self.original_color))

    def highlight_hierarchy(self):
        # Highlight this form
        self.highlight()

        # Highlight parent form if it exists
        if self.parent_form:
            self.parent_form.highlight_hierarchy()

    def set_focus_to_input(self):
        self.input_text_edit.setFocus()

    def moveBy(self, dx, dy):
        super().moveBy(dx, dy)
        self.update_link_lines()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_item.setRect(self.boundingRect())
        self.update_resize_handle()

    def mousePressEvent(self, event):
        self.setFocus()
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.header.boundingRect().contains(event.pos())
            and not self.circle_item.isUnderMouse()
        ):
            super().mousePressEvent(event)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable and not self.circle_item.isUnderMouse():
            super().mouseMoveEvent(event)
            self.update_link_lines()
        else:
            event.ignore()

    def generate_follow_up_questions(self):
        # Gather the current conversation context
        context_data = []
        for _i, data in enumerate(self.gather_form_data()):
            context = data["context"]
            if context:
                message = {"role": "user", "content": context}
                context_data.append(message)

        # Construct the prompt for generating follow-up questions
        prompt = (
            "Based on the conversation above,"
            "please generate 3 follow-up questions."
            "Keep them concise and relevant to the topic."
            "Just list the 3 questions without any other text."
            "Do not prefix the questions with a number."
        )
        context_data.append({"role": "user", "content": prompt})

        self.highlight_hierarchy()
        self.start_processing()

        self.setup_llm_worker(context_data, update_handler=self.handle_follow_up_questions)

    def handle_follow_up_questions(self, text):
        try:
            questions = text.split("\n")
            form_width = self.boundingRect().width()
            form_height = self.boundingRect().height()
            x_offset = form_width + 200
            for i, question in enumerate(questions):
                if question.strip():
                    y_offset = i * (form_height + 50)
                    new_pos = self.pos() + QPointF(x_offset, y_offset)
                    command = CreateFormCommand(self.scene(), self, new_pos, self.model)
                    self.scene().command_invoker.execute(command)
                    new_form = command.created_form
                    new_form.input_box.widget().setPlainText(question)
        except Exception as e:
            self.handle_error(f"Error parsing follow-up questions: {e!s}")

    def clone_branch(self):
        self.logger.info("Initiating branch cloning operation")
        try:
            command = CloneBranchCommand(self.scene(), self)
            self.scene().command_invoker.execute(command)
            self.logger.info("Branch cloned successfully")
        except Exception:
            self.logger.exception("Failed to clone branch: %s")
            raise

    def clone_form(self):
        self.logger.info("Initiating form cloning operation")
        try:
            form_width = self.boundingRect().width()
            min_gap = 100

            # Generate random offset for more natural spread
            random_offset_x = random.randint(min_gap, min_gap * 3)
            random_offset_y = random.randint(min_gap, min_gap * 3)

            self.logger.debug("Clone position offset: x=%s, y=%s", random_offset_x, random_offset_y)

            # Calculate top right position instead of bottom right
            clone_pos = self.pos() + QPointF(form_width + random_offset_x, -random_offset_y)

            command = CreateFormCommand(self.scene(), self, clone_pos, self.model)
            self.scene().command_invoker.execute(command)
            self.logger.info("Form cloned successfully at position (%.1f, %.1f)", clone_pos.x(), clone_pos.y())
        except Exception:
            self.logger.exception("Failed to clone form: %s")
            raise

    def delete_form(self):
        self.logger.info("Initiating form deletion operation")
        try:
            command = DeleteFormCommand(self)
            self.scene().command_invoker.execute(command)
            self.logger.info("Form deleted successfully")
        except Exception:
            self.logger.exception("Failed to delete form: %s")
            raise

    def update_link_lines(self):
        if self.link_line:
            self.link_line.update_position()
        for child in self.child_forms:
            child.update_link_lines()

    def all_forms(self):
        self.form_chain.appendleft(self)
        current_form = self
        while current_form:
            current_form = current_form.parent_form
            if current_form:
                self.form_chain.appendleft(current_form)

    def process_next_form(self):
        try:
            form = self.form_chain.popleft()
            question = form.input_box.widget().toPlainText().strip()
            self.logger.info("Processing form with question: %s", question)
            form.submit_form()
            form.llm_worker.signals.notify_child.connect(self.process_next_form)
        except IndexError:
            self.logger.info("Processed all forms in chain")

    def re_run_all(self):
        self.all_forms()
        self.process_next_form()

    def submit_search(self):
        input_text = self.input_box.widget().toPlainText().strip()
        if not input_text:
            self.logger.debug("Search submission cancelled: empty input text")
            return

        query_display = input_text[:100] + ("..." if len(input_text) > 100 else "")
        self.logger.info("Initiating search operation for query: '%s'", query_display)
        self.logger.debug("Search query length: %s characters", len(input_text))

        self.highlight_hierarchy()
        self.start_processing()
        self.setup_search_worker(input_text, update_handler=self.handle_update)

    def submit_form(self):
        input_text = self.input_box.widget().toPlainText().strip()
        if not input_text:
            return

        # Check if the input is a URL
        url_pattern = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        if url_pattern.match(input_text):
            self.fetch_jina_reader_content(input_text)
        else:
            self.process_llm_request(input_text)

    def fetch_jina_reader_content(self, url):
        main_window = self.scene().views()[0].window()
        jina_api_key = main_window.jina_api_key

        self.jina_worker = JinaReaderWorker(url, jina_api_key)
        self.jina_worker.signals.result.connect(self.handle_jina_reader_content)
        self.jina_worker.signals.error.connect(self.handle_error)

        self.highlight_hierarchy()
        thread_pool.start(self.jina_worker)
        self.start_processing()

    def handle_jina_reader_content(self, content):
        context_with_prompt = f"""
        Summarize the following content:
        {content}
        """
        context_data = [{"role": "user", "content": context_with_prompt}]
        self.setup_llm_worker(context_data, update_handler=self.handle_update)

    def process_llm_request(self, input_text):
        self.logger.info("Processing LLM request with model: %s", self.model)
        self.logger.debug("Input text length: %d characters", len(input_text))

        form_data = self.gather_form_data()
        context_data = []
        for data in form_data:
            context = data["context"]
            if context:
                message = {"role": "user", "content": context}
                context_data.append(message)

        self.logger.debug("Gathered %s context messages from form hierarchy", len(context_data))

        selected_files = self.picker.get_selected_files()
        self.logger.debug("Processing %s selected files", len(selected_files))
        for selected_file in selected_files:
            try:
                file_content = Path(selected_file).read_text(encoding="utf-8")
                file_message = {"role": "user", "content": linesep.join([selected_file, file_content])}
                context_data.append(file_message)
                self.logger.debug("Successfully loaded file: %s (%d chars)", selected_file, len(file_content))
            except OSError:
                self.logger.exception("Unable to open file %s")

        current_message = {"role": "user", "content": input_text}
        context_data.append(current_message)

        self.logger.info("Total context messages prepared: %s", len(context_data))

        self.highlight_hierarchy()
        self.start_processing()
        self.setup_llm_worker(context_data, update_handler=self.handle_update)

    def setup_llm_worker(self, context, update_handler):
        self.logger.info("Setting up LLM worker with model: %s", self.model)
        self.logger.debug(
            f"System message: {self.system_message[:100]}..."
            if len(self.system_message) > 100
            else f"System message: {self.system_message}"
        )
        self.logger.debug("Context contains %s messages", len(context))

        try:
            self.llm_worker = LlmWorker(self.model, self.system_message, context)
            self.llm_worker.signals.update.connect(update_handler)
            self.llm_worker.signals.finished.connect(self.handle_finished)
            self.llm_worker.signals.error.connect(self.handle_error)

            global active_workers
            active_workers += 1
            self.logger.info("Starting LLM worker (active workers: %s)", active_workers)
            thread_pool.start(self.llm_worker)
            self.logger.debug("LLM worker successfully added to thread pool")
        except Exception:
            self.logger.exception("Failed to setup LLM worker: %s")
            raise

    def setup_search_worker(self, search_query, update_handler):
        query_display = search_query[:50] + ("..." if len(search_query) > 50 else "")
        self.logger.info("Setting up search worker for query: '%s'", query_display)
        self.logger.debug("Search query: %s", search_query)

        try:
            self.search_worker = SearchWorker(search_query)
            self.search_worker.signals.result.connect(update_handler)
            self.search_worker.signals.error.connect(self.handle_error)

            global active_workers
            active_workers += 1
            self.logger.info("Starting search worker (active workers: %s)", active_workers)
            thread_pool.start(self.search_worker)
            self.logger.debug("Search worker successfully added to thread pool")
        except Exception:
            self.logger.exception("Failed to setup search worker: %s")
            raise

    def start_processing(self):
        global active_workers
        active_workers += 1
        self.logger.debug("Started processing (total active workers: %s)", active_workers)
        self.header.start_processing()

    def stop_processing(self):
        global active_workers
        active_workers -= 1
        self.logger.debug("Stopped processing (total active workers: %s)", active_workers)
        self.header.stop_processing()
        if self.llm_worker:
            self.llm_worker.signals.notify_child.emit()

    def on_model_changed(self, new_model):
        self.model = new_model

    def handle_update(self, text):
        self.logger.debug("Received worker update: %s characters", len(text))
        self.stop_processing()
        self.update_answer(text)

    def handle_finished(self):
        global active_workers
        active_workers = max(0, active_workers - 1)
        self.logger.info("LLM worker finished successfully (active workers: %s)", active_workers)
        self.stop_processing()

    def handle_error(self, error):
        global active_workers
        active_workers = max(0, active_workers - 1)
        self.logger.error("LLM worker error (active workers: %d): %s", active_workers, error)
        self.stop_processing()
        self.update_answer(f"Error occurred: {error}")

    def update_answer(self, message):
        self.markdown_content = message
        conversation_widget = self.conversation_area.widget()
        renderer = HtmlRenderer()
        conversation_widget.setDocument(renderer.render(self.markdown_content))

    def gather_form_data(self):
        data = []
        current_form = self.parent_form
        while current_form:
            form_data = {
                "context": current_form.conversation_area.widget().toPlainText(),
            }
            data.append(form_data)
            current_form = current_form.parent_form
        return reversed(data)

    def to_dict(self):
        return {
            "pos_x": self.pos().x(),
            "pos_y": self.pos().y(),
            "width": self.size().width(),
            "height": self.size().height(),
            "input": self.input_box.widget().toPlainText(),
            "context": self.markdown_content,
            "children": [child.to_dict() for child in self.child_forms],
            "model": self.model,
            "selected_files": self.picker.get_selected_files(),
        }

    @classmethod
    def from_dict(cls, data, scene, parent=None):
        form: FormWidget = cls(parent, model=data["model"])
        form.setPos(QPointF(data["pos_x"], data["pos_y"]))

        width = data.get("width", 300)
        height = data.get("height", 200)
        form.resize(width, height)

        form.input_box.widget().setPlainText(data["input"])
        form.markdown_content = data["context"]
        form.update_answer(form.markdown_content)
        if "model" in data:
            form.model = data["model"]
            form.header.update_model_name()
        if "selected_files" in data:
            form.picker.set_selected_files(data["selected_files"])

        scene.addItem(form)

        for child_data in data["children"]:
            child = cls.from_dict(child_data, scene, form)
            form.child_forms.append(child)
            link_line = LinkLine(form, child)
            scene.addItem(link_line)
            child.link_line = link_line

        return form

    def setup_conversation_widget(self, widget):
        """Configure the conversation widget with link handling and interaction flags"""
        widget.setOpenExternalLinks(False)
        widget.anchorClicked.connect(self.handle_link_click)
        widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        widget.customContextMenuRequested.connect(self.show_context_menu)

    def handle_link_click(self, url):
        """Handle clicks on links by opening them in the default browser"""
        import webbrowser

        webbrowser.open(url.toString())


class JsonCanvasExporter:
    def __init__(self, scene):
        self.scene = scene

    def export(self, file_name):
        nodes = []
        edges = []
        form_ids = {}

        for _i, item in enumerate(self.scene.items()):
            if isinstance(item, FormWidget) and not item.parent_form:
                form_id = str(uuid.uuid4())
                form_ids[item] = form_id
                nodes.append(self.form_to_json_canvas_node(item, form_id))
                self.export_child_forms(item, form_id, nodes, edges, form_ids)

        canvas_data = {"nodes": nodes, "edges": edges}

        with Path(file_name).open("w") as f:
            json.dump(canvas_data, f, indent=2)

    def export_child_forms(self, form, parent_id, nodes, edges, form_ids):
        for child in form.child_forms:
            child_id = str(uuid.uuid4())
            form_ids[child] = child_id
            nodes.append(self.form_to_json_canvas_node(child, child_id))
            edges.append(self.create_edge(parent_id, child_id))
            self.export_child_forms(child, child_id, nodes, edges, form_ids)

    def form_to_json_canvas_node(self, form, form_id):
        rect = form.mapToScene(form.boundingRect()).boundingRect()
        x = int(rect.x())
        y = int(rect.y())
        width = int(rect.width())
        height = int(rect.height())

        return {
            "id": form_id,
            "type": "text",
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "text": form.input_box.widget().toPlainText() + "\n\n" + form.conversation_area.widget().toPlainText(),
        }

    def create_edge(self, source_id, target_id):
        edge_id = str(uuid.uuid4())
        return {
            "id": edge_id,
            "fromNode": source_id,
            "toNode": target_id,
        }


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger("config_dialog")
        self.logger.debug("Initializing configuration dialog")

        self.setWindowTitle("Configuration")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Jina API Key input
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Jina API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        layout.addLayout(api_key_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Connect buttons
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.logger.info("Configuration dialog initialized successfully")

    def get_jina_api_key(self):
        api_key = self.api_key_input.text()
        self.logger.debug("Retrieved Jina API key from dialog: %s", "[SET]" if api_key else "[EMPTY]")
        return api_key

    def set_jina_api_key(self, jina_api_key):
        self.logger.debug("Setting Jina API key in dialog: %s", "[SET]" if jina_api_key else "[EMPTY]")
        self.api_key_input.setText(jina_api_key)


class StateManager:
    def __init__(self, company, application):
        self.settings = QSettings(company, application)
        self.keyring_service = f"{company}-{application}"
        self.logger = get_logger("state_manager")
        self.logger.info("StateManager initialized for %s-%s", company, application)

    def save_window_state(self, window):
        self.logger.debug("Saving window state (geometry and state)")
        try:
            self.settings.setValue("window_geometry", window.saveGeometry())
            self.settings.setValue("window_state", window.saveState())
            self.logger.info("Window state saved successfully")
        except Exception:
            self.logger.exception("Failed to save window state: %s")
            raise

    def restore_window_state(self, window):
        self.logger.debug("Attempting to restore window state")
        try:
            geometry = self.settings.value("window_geometry")
            state = self.settings.value("window_state")

            if geometry and state:
                window.restoreGeometry(geometry)
                window.restoreState(state)
                self.logger.info("Window state restored successfully")
                return True
            self.logger.debug("No saved window state found")
            return False
        except Exception:
            self.logger.exception("Failed to restore window state: %s")
            return False

    def save_last_file(self, file_path):
        self.logger.debug("Saving last file path: %s", file_path)
        try:
            self.settings.setValue("last_file", file_path)
            self.logger.info("Last file path saved: %s", file_path)
        except Exception:
            self.logger.exception("Failed to save last file path: %s")
            raise

    def get_last_file(self):
        try:
            last_file = self.settings.value("last_file")
            self.logger.debug("Retrieved last file path: %s", last_file)
            return last_file
        except Exception:
            self.logger.exception("Failed to get last file path: %s")
            return None

    def clear_settings(self):
        self.logger.info("Clearing all application settings")
        try:
            self.settings.clear()
            self.logger.info("Application settings cleared successfully")
        except Exception:
            self.logger.exception("Failed to clear settings: %s")
            raise

    def save_jina_api_key(self, jina_api_key):
        self.logger.debug("Saving Jina API key to keyring")
        try:
            keyring.set_password(self.keyring_service, "jina_api_key", jina_api_key)
            self.logger.info("Jina API key saved successfully to keyring")
        except Exception:
            self.logger.exception("Failed to save Jina API key: %s")
            raise

    def get_jina_api_key(self):
        try:
            api_key = keyring.get_password(self.keyring_service, "jina_api_key") or ""
            self.logger.debug("Retrieved Jina API key from keyring: %s", "[SET]" if api_key else "[NOT SET]")
            return api_key
        except Exception:
            self.logger.exception("Failed to get Jina API key: %s")
            return ""

    def clear_jina_api_key(self):
        self.logger.info("Clearing Jina API key from keyring")
        try:
            keyring.delete_password(self.keyring_service, "jina_api_key")
            self.logger.info("Jina API key cleared successfully from keyring")
        except Exception:
            self.logger.exception("Failed to clear Jina API key: %s")
            raise


class MiniMap(QGraphicsView):
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.setScene(QGraphicsScene(self))
        self.setFixedSize(200, 150)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background: rgba(200, 200, 200, 150); border: 1px solid gray;")
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

        viewport_rect = self.main_view.mapToScene(self.main_view.viewport().rect()).boundingRect()
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
        initial_scrollbar_value = int(((self.current_zoom - self.min_zoom) / (self.max_zoom - self.min_zoom)) * 100)
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
        available_width = self._instruction_rect.width() - 20  # 10px padding on each side
        available_height = self._instruction_rect.height() - 20  # 10px padding on top and bottom

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
        text_width = max(fm.horizontalAdvance(line) for line in self.instruction_text.split("\n"))
        text_height = fm.height() * len(self.instruction_text.split("\n"))
        padding = 10
        self.full_width = text_width + 2 * padding
        self.full_height = text_height + 2 * padding
        self.small_width = 30
        self.small_height = 30

        if self.is_expanded:
            self._instruction_rect = QRectF(padding, padding, self.full_width, self.full_height)
        else:
            self._instruction_rect = QRectF(padding, padding, self.small_width, self.small_height)

    def start_animation(self):
        if self.is_expanded:
            self.is_expanded = False
            self.update_instruction_rect()
            self.animation.setStartValue(QRectF(10, 10, self.full_width, self.full_height))
            self.animation.setEndValue(QRectF(10, 10, self.small_width, self.small_height))
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
        if (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ShiftModifier) or (
            event.button() == Qt.MouseButton.MiddleButton
        ):
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
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
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
        if self.is_selecting and (
            (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            or (event.button() == Qt.MouseButton.MiddleButton)
        ):
            self.is_selecting = False
            if self.rubberBand:
                self.rubberBand.hide()
                selection_rect = self.mapToScene(self.rubberBand.geometry()).boundingRect()
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
        scrollbar_value = int(((self.current_zoom - self.min_zoom) / (self.max_zoom - self.min_zoom)) * 100)
        self.zoom_scrollbar.setValue(scrollbar_value)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom_in_factor = 1.2
            zoom_out_factor = 1 / zoom_in_factor

            zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor

            resulting_zoom = self.current_zoom * zoom_factor
            if self.min_zoom <= resulting_zoom <= self.max_zoom:
                self.current_zoom = resulting_zoom
                self.zoom_to(self.current_zoom)

                # Update scrollbar value
                scrollbar_value = int(((self.current_zoom - self.min_zoom) / (self.max_zoom - self.min_zoom)) * 100)
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


class GraphicsScene(QGraphicsScene):
    itemAdded = pyqtSignal()
    itemMoved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_invoker = CommandInvoker()
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.itemMoved.emit)
        self.logger = get_logger("scene")

    def addItem(self, item):
        super().addItem(item)
        self.itemAdded.emit()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.update_timer.start(100)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.create_new_form(event.scenePos())
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            view = self.views()[0]
            center = view.mapToScene(view.viewport().rect().center())
            self.create_new_form(center)
        else:
            super().keyPressEvent(event)

    def apply_expansion_recursively(self, expand=True):
        for item in self.items():
            if isinstance(item, FormWidget):
                self._apply_expansion_to_form(item, expand)

    def _apply_expansion_to_form(self, form, expand):
        form.expand_form()

    def create_new_form(self, position):
        self.logger.info("Creating new form at position (%.1f, %.1f)", position.x(), position.y())
        try:
            command = CreateFormCommand(self)
            self.command_invoker.execute(command)
            new_form = command.created_form
            new_form.setPos(position)
            self.logger.info("New form created successfully")
            return new_form
        except Exception:
            self.logger.exception("Failed to create new form: %s")
            raise


class MainWindow(QMainWindow):
    def __init__(self, auto_load_state=True):
        super().__init__()
        self.logger = get_logger("mainwindow")
        self.state_manager = StateManager("deskriders", "chatcircuit")
        self.setWindowTitle(APPLICATION_TITLE)

        self.scene = GraphicsScene()
        self.view = CustomGraphicsView(self.scene, initial_zoom=1.0)
        self.view.zoomChanged.connect(self.on_zoom_changed)
        self.setCentralWidget(self.view)

        self.zoom_factor = 1.0
        self.create_menu()

        self.is_updating_scene_rect = False

        self.jina_api_key = self.state_manager.get_jina_api_key()

        if auto_load_state:
            self.restore_application_state()

    def export_to_markdown(self):
        """Export all chat content to a markdown file."""
        self.logger.info("Initiating markdown export")
        file_name, _ = QFileDialog.getSaveFileName(self, "Export to Markdown", "", "Markdown Files (*.md)")

        if not file_name:
            self.logger.info("Markdown export cancelled by user")
            return

        self.logger.info("Exporting to markdown file: %s", file_name)
        markdown_content = []

        # Get content from all root forms (forms without parents)
        root_forms_count = 0
        for item in self.scene.items():
            if isinstance(item, FormWidget) and not item.parent_form:
                markdown_content.append(item.get_markdown_hierarchy())
                root_forms_count += 1

        self.logger.debug("Collected content from %s root forms", root_forms_count)

        # Write to file
        try:
            content_text = "\n\n".join(markdown_content)
            with Path(file_name).open("w", encoding="utf-8") as f:
                f.write(content_text)

            file_size = Path(file_name).stat().st_size
            self.logger.info(
                "Successfully exported to %s (%d bytes, %d characters)", file_name, file_size, len(content_text)
            )

            QMessageBox.information(
                self,
                "Export Successful",
                f"Chat content has been exported to {file_name}",
            )
        except Exception as e:
            self.logger.exception("Failed to export to markdown %s: %s", file_name)
            QMessageBox.critical(self, "Export Failed", f"Failed to export chat content: {e!s}")

    def update_scene_rect(self):
        self.scene.apply_expansion_recursively(True)

        if self.is_updating_scene_rect:
            return
        self.is_updating_scene_rect = True

        # Calculate the bounding rect of all items
        items_rect = QRectF()
        for item in self.scene.items():
            items_rect = items_rect.united(item.sceneBoundingRect())

        # Add some margin
        margin = 1000
        new_rect = items_rect.adjusted(-margin, -margin, margin, margin)

        # Update the scene rect
        self.scene.setSceneRect(new_rect)
        self.view.updateSceneRect(new_rect)

        self.is_updating_scene_rect = False

    def on_zoom_changed(self, zoom_factor):
        self.zoom_factor = zoom_factor
        self.update_zoom()

    def create_menu(self):
        # File menu
        file_menu = self.menuBar().addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_state)
        file_menu.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        load_action.triggered.connect(self.load_state)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        export_markdown_action = QAction("Export to Markdown", self)
        export_markdown_action.setShortcut(QKeySequence("Ctrl+Shift+M"))
        export_markdown_action.triggered.connect(self.export_to_markdown)
        file_menu.addAction(export_markdown_action)

        export_action = QAction("Export to JSON Canvas", self)
        export_action.triggered.connect(self.export_to_json_canvas)
        file_menu.addAction(export_action)

        # New PNG export action
        export_png_action = QAction("Export to PNG", self)
        export_png_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
        export_png_action.triggered.connect(self.export_to_png)
        file_menu.addAction(export_png_action)

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

        view_menu.addSeparator()

        fit_scene_action = QAction("Fit Scene", self)
        fit_scene_action.setShortcut(QKeySequence("Ctrl+R"))
        fit_scene_action.triggered.connect(self.update_scene_rect)
        view_menu.addAction(fit_scene_action)

        config_menu = self.menuBar().addMenu("Configuration")

        api_config_action = QAction("API Configuration", self)
        api_config_action.triggered.connect(self.show_config_dialog)
        config_menu.addAction(api_config_action)

        config_menu.addSeparator()

        open_logs_action = QAction("Open Log Directory", self)
        open_logs_action.triggered.connect(self.open_log_directory)
        config_menu.addAction(open_logs_action)

    def show_config_dialog(self):
        self.logger.info("Opening configuration dialog")
        try:
            dialog = ConfigDialog(self)
            dialog.set_jina_api_key(self.jina_api_key)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.logger.info("Configuration dialog accepted, saving settings")
                self.jina_api_key = dialog.get_jina_api_key()
                self.state_manager.save_jina_api_key(self.jina_api_key)
                self.logger.info("Configuration saved successfully")
                QMessageBox.information(self, "Configuration", "Jina API Key saved successfully!")
            else:
                self.logger.info("Configuration dialog cancelled by user")
        except Exception as e:
            self.logger.exception("Error in configuration dialog: %s")
            QMessageBox.critical(self, "Configuration Error", f"Failed to save configuration: {e}")

    def open_log_directory(self):
        """Open the log directory in the system's file manager."""
        self.logger.info("Opening log directory in file manager")
        try:
            log_dir = get_log_directory()
            self.logger.debug("Log directory path: %s", log_dir)

            # Ensure the directory exists
            if not log_dir.exists():
                self.logger.warning("Log directory does not exist: %s", log_dir)
                QMessageBox.warning(self, "Log Directory", f"Log directory does not exist:\n{log_dir}")
                return

            # Open directory in system file manager
            import subprocess
            import sys

            if sys.platform == "darwin":  # macOS
                subprocess.run(["/usr/bin/open", str(log_dir)], check=True)  # noqa: S603
            elif sys.platform == "win32":  # Windows
                subprocess.run(["C:\\Windows\\system32\\explorer.exe", str(log_dir)], check=True)  # noqa: S603
            else:  # Linux and other Unix-like systems
                subprocess.run(["/usr/bin/xdg-open", str(log_dir)], check=True)  # noqa: S603

            self.logger.info("Successfully opened log directory: %s", log_dir)

        except Exception as e:
            self.logger.exception("Failed to open log directory: %s")
            QMessageBox.critical(self, "Error", f"Failed to open log directory:\n{e}")

    def export_to_png(self):
        """Export the entire canvas as a high-quality PNG image."""
        self.logger.info("Initiating PNG export")
        file_name, _ = QFileDialog.getSaveFileName(self, "Export to PNG", "", "PNG Files (*.png)")

        if not file_name:
            self.logger.info("PNG export cancelled by user")
            return

        self.logger.info("Exporting canvas to PNG: %s", file_name)

        try:
            # Calculate the scene bounding rect
            scene_rect = self.scene.itemsBoundingRect()
            scene_rect = scene_rect.adjusted(-100, -100, 100, 100)  # Add some padding
            self.logger.debug("Scene rect for export: %dx%d", scene_rect.width(), scene_rect.height())

            # Render the scene to a QImage
            image = QImage(scene_rect.size().toSize(), QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)  # Fill with white background
            painter = QPainter(image)
            self.scene.render(painter, QRectF(image.rect()), scene_rect)
            painter.end()

            # Save the image
            if image.save(file_name, "PNG", 100):
                file_size = Path(file_name).stat().st_size
                self.logger.info(
                    "Successfully exported PNG to %s (%d bytes, %dx%dx)",
                    file_name,
                    file_size,
                    image.width(),
                    image.height(),
                )
                QMessageBox.information(self, "Export Successful", f"Canvas has been exported to {file_name}")
            else:
                self.logger.error("Failed to save PNG image to %s", file_name)
                QMessageBox.critical(self, "Export Failed", "Failed to export canvas to PNG.")
        except Exception as e:
            self.logger.exception("Error during PNG export to %s: %s", file_name)
            QMessageBox.critical(self, "Export Failed", f"Failed to export canvas to PNG: {e}")

    def export_to_json_canvas(self):
        self.logger.info("Initiating JSON Canvas export")
        file_name, _ = QFileDialog.getSaveFileName(self, "Export to JSON Canvas", "", "Canvas Files (*.canvas)")
        if not file_name:
            self.logger.info("JSON Canvas export cancelled by user")
            return

        self.logger.info("Exporting to JSON Canvas file: %s", file_name)
        try:
            exporter = JsonCanvasExporter(self.scene)
            exporter.export(file_name)

            file_size = Path(file_name).stat().st_size
            self.logger.info("Successfully exported to JSON Canvas: %s (%d bytes)", file_name, file_size)
        except Exception:
            self.logger.exception("Failed to export to JSON Canvas %s: %s", file_name)
            raise

    def new_document(self):
        self.state_manager.save_last_file("")
        self.scene.clear()
        self.save_state()

    def save_state(self):
        self.logger.info("Initiating save state operation")
        file_name = self.state_manager.get_last_file()
        if not file_name:
            self.logger.debug("No previous file found, opening save dialog")
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "JSON Files (*.json)")

        if not file_name:
            self.logger.info("Save operation cancelled by user")
            return

        self.logger.info("Saving state to file: %s", file_name)

        try:
            states = []
            for item in self.scene.items():
                if isinstance(item, FormWidget) and not item.parent_form:
                    states.append(item.to_dict())

            self.logger.debug("Collected %s form states for saving", len(states))

            document_data = {"zoom_factor": self.zoom_factor, "canvas_state": states}
            with Path(file_name).open("w") as f:
                json.dump(document_data, f, indent=2)

            file_size = Path(file_name).stat().st_size
            self.logger.info("Successfully saved state to %s (%d bytes)", file_name, file_size)

            self.setWindowTitle(f"{APPLICATION_TITLE} - {file_name}")
            self.state_manager.save_last_file(file_name)
        except Exception:
            self.logger.exception("Failed to save state to %s: %s", file_name)
            raise

    def load_state(self):
        self.logger.info("Initiating load state operation")
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")

        if not file_name:
            self.logger.info("Load operation cancelled by user")
            return

        if Path(file_name).exists():
            self.logger.info("Loading state from file: %s", file_name)
            self.state_manager.save_last_file(file_name)
            self.load_from_file(file_name)
        else:
            self.logger.warning("File %s not found.", file_name)

    def load_from_file(self, file_name):
        self.logger.debug("Loading from file: %s", file_name)

        try:
            if Path(file_name).exists():
                file_size = Path(file_name).stat().st_size
                self.logger.debug("File size: %s bytes", file_size)

                with Path(file_name).open() as f:
                    document_data = json.load(f)
            else:
                self.logger.error("File not found: %s", file_name)
                raise LookupError(f"Unable to find file {file_name}")

            self.zoom_factor = document_data.get("zoom_factor", self.zoom_factor)
            self.logger.debug("Restored zoom factor: %s", self.zoom_factor)
            self.view.zoom_to(self.zoom_factor)

            canvas_state = document_data.get("canvas_state", [])
            self.logger.debug("Loading %s form states", len(canvas_state))

            self.scene.clear()
            for form_data in canvas_state:
                FormWidget.from_dict(form_data, self.scene)

            self.setWindowTitle(f"{APPLICATION_TITLE} - {file_name}")
            self.logger.info("Successfully loaded state from %s (%d forms)", file_name, len(canvas_state))
        except Exception:
            self.logger.exception("Failed to load from file %s: %s", file_name)
            raise

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

    def restore_application_state(self):
        if not self.state_manager.restore_window_state(self):
            self.showMaximized()

        file_name = self.state_manager.get_last_file()
        if file_name and isinstance(file_name, str) and Path(file_name).exists():
            self.load_from_file(file_name)
        else:
            QMessageBox.warning(self, "Error", f"Failed to load the last file: {file_name}")

    def closeEvent(self, event):
        self.logger.info("Application shutdown initiated")
        self.state_manager.save_window_state(self)
        self.save_state()
        self.logger.info("Application state saved successfully")
        super().closeEvent(event)
        self.logger.info("Application shutdown completed")


def main():
    logger.info("Starting %s application", APPLICATION_TITLE)
    app = QApplication(sys.argv)

    # Try to set the application icon, but don't fail if it's not available
    try:
        # Try multiple icon formats
        icon_formats = ["resources/icon.png", "resources/icon.ico", "resources/icon.icns"]
        icon_loaded = False

        for icon_file in icon_formats:
            icon_path = resource_path(icon_file)
            logger.debug("Trying to load application icon from: %s", icon_path)

            if Path(icon_path).exists():
                try:
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        app.setWindowIcon(icon)
                        logger.info("Application icon loaded successfully from: %s", icon_file)
                        icon_loaded = True
                        break
                    logger.debug("Icon file exists but QIcon is null: %s", icon_path)
                except Exception as icon_error:
                    logger.debug("Failed to load icon %s: %s", icon_path, icon_error)
            else:
                logger.debug("Icon file not found: %s", icon_path)

        if not icon_loaded:
            logger.info("No application icon loaded - using default")

    except Exception as e:
        logger.warning("Error during application icon loading: %s", e)

    try:
        window = MainWindow()
        window.show()
        logger.info("Application window displayed successfully")
        exit_code = app.exec()
        logger.info("Application exiting with code: %s", exit_code)
        sys.exit(exit_code)
    except Exception as e:
        logger.critical("Critical error during application startup: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
