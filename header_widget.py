from PyQt6.QtWidgets import QGraphicsWidget, QGraphicsProxyWidget, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QBrush


class HeaderWidget(QGraphicsWidget):
    def __init__(self):
        super().__init__()

        # Initialize all attributes
        self.progress_bar = None
        self.is_initialized = False

        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

        # Schedule the creation of the progress bar for the next event loop iteration
        QTimer.singleShot(0, self.create_progress_bar)

    def create_progress_bar(self):
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

        self.is_initialized = True
        self.updateProgressBarGeometry()

    def updateProgressBarGeometry(self):
        if self.is_initialized and self.progress_bar:
            rect = QRectF(0, self.boundingRect().height() - 10,
                          self.boundingRect().width(), 10)
            self.progress_bar.setGeometry(rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateProgressBarGeometry()

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
