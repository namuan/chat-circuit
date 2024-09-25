from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QGraphicsProxyWidget, QPushButton, QGraphicsLinearLayout


def create_svg_icon(file_path):
    icon = QIcon(file_path)
    return icon


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


def add_buttons(form_widget):
    bottom_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)

    # Define button configurations
    buttons = [
        ("resources/ripple.svg", "Re-Run", form_widget.re_run_all),
        ("resources/fork.svg", "Fork", form_widget.clone_form),
        ("resources/clone.svg", "Clone Branch", form_widget.clone_branch),
        (
            "resources/bulb.svg",
            "Follow-up Questions",
            form_widget.generate_follow_up_questions,
        ),
        ("resources/delete.svg", "Delete", form_widget.delete_form),
    ]

    # Create and add buttons
    for icon_path, tooltip, callback in buttons:
        button_widget = create_button(icon_path, tooltip, callback)
        bottom_layout.addItem(button_widget)

    return bottom_layout
