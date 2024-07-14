from PyQt6.QtWidgets import QGraphicsWidget, QGraphicsProxyWidget, QProgressBar, QLabel
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QBrush, QFont


class HeaderWidget(QGraphicsWidget):
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
        progress_bar_widget.setTextVisible(False)  # Hide the text
        progress_bar_widget.setFixedHeight(10)  # Make it smaller
        progress_bar_widget.setStyleSheet("""
            QProgressBar {
                background-color: transparent;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)

        self.progress_bar = QGraphicsProxyWidget(self)
        self.progress_bar.setWidget(progress_bar_widget)
        self.progress_bar.hide()

        # Create model label
        model_label_widget = QLabel()
        model_label_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        model_label_widget.setStyleSheet("color: #333; font-weight: bold;")
        model_label_widget.setFont(QFont("Arial", 10))

        self.model_label = QGraphicsProxyWidget(self)
        self.model_label.setWidget(model_label_widget)

        self.is_initialized = True
        self.updateWidgetGeometry()

    def updateWidgetGeometry(self):
        if self.is_initialized:
            header_rect = self.boundingRect()

            # Position the model label
            self.model_label.setGeometry(QRectF(5, 5, header_rect.width() - 10, 20))

            # Position the progress bar at the bottom
            self.progress_bar.setGeometry(QRectF(0, header_rect.height() - 10, header_rect.width(), 10))
            self.update_model_name()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateWidgetGeometry()

    def paint(self, painter, option, widget):
        painter.fillRect(self.boundingRect(), QBrush(QColor(200, 200, 200)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)

    def start_processing(self):
        if self.is_initialized and self.progress_bar:
            self.progress_bar.show()

    def stop_processing(self):
        if self.is_initialized and self.progress_bar:
            self.progress_bar.hide()

    def update_model_name(self):
        if self.is_initialized:
            self.model_label.widget().setText(f"Model: {self.model_name}")
