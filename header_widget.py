from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGraphicsProxyWidget,
    QGraphicsWidget,
    QProgressBar,
)

from models import LLM_MODELS


class HeaderWidget(QGraphicsWidget):
    model_changed = pyqtSignal(str)

    def __init__(self, model_name):
        super().__init__()

        # Initialize all attributes
        self.model_name = model_name

        self.progress_bar = None
        self.model_label = None
        self.is_initialized = False

        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

        # Schedule the creation of the progress bar and model label for the next event loop iteration
        QTimer.singleShot(0, self.create_widgets)

    def create_widgets(self):
        # Create progress bar
        progress_bar_widget = QProgressBar()
        progress_bar_widget.setRange(0, 0)  # Set to indeterminate mode
        progress_bar_widget.setTextVisible(False)
        progress_bar_widget.setFixedHeight(20)
        progress_bar_widget.setStyleSheet(
            """
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """
        )

        self.progress_bar = QGraphicsProxyWidget(self)
        self.progress_bar.setWidget(progress_bar_widget)
        self.progress_bar.hide()

        # Create model dropdown
        model_dropdown_widget = QComboBox()
        model_dropdown_widget.addItems(LLM_MODELS)
        model_dropdown_widget.setStyleSheet(
            """
            QComboBox {
                padding: 1px 18px 1px 3px;
                min-width: 6em;
                background: darkgray;
            }
        """
        )
        model_dropdown_widget.currentTextChanged.connect(self.on_model_changed)

        self.model_dropdown = QGraphicsProxyWidget(self)
        self.model_dropdown.setWidget(model_dropdown_widget)

        self.is_initialized = True
        self.updateWidgetGeometry()

    def updateWidgetGeometry(self):
        if self.is_initialized:
            header_rect = self.boundingRect()
            # Position the model dropdown
            self.model_dropdown.setGeometry(QRectF(0, 0, header_rect.width(), 30))
            # Position the progress bar at the bottom
            self.progress_bar.setGeometry(
                QRectF(0, header_rect.height() - 15, header_rect.width(), 5)
            )
            self.update_model_name()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateWidgetGeometry()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)

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
            self.model_dropdown.widget().setCurrentText(self.model_name)
