import random

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout, QGraphicsItem, QMessageBox, QGraphicsProxyWidget, \
    QLabel, QLineEdit, QPushButton

from header_widget import HeaderWidget


class FormWidget(QGraphicsWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.parent_form = parent
        self.child_forms = []
        self.link_line = None

        # Create main layout
        main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Create and add header
        self.header = HeaderWidget()
        main_layout.addItem(self.header)

        # Create form layout
        form_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Create form elements and their proxies
        name_label = QGraphicsProxyWidget()
        name_label.setWidget(QLabel("Name:"))

        self.name_input = QGraphicsProxyWidget()
        self.name_input.setWidget(QLineEdit())

        email_label = QGraphicsProxyWidget()
        email_label.setWidget(QLabel("Email:"))

        self.email_input = QGraphicsProxyWidget()
        self.email_input.setWidget(QLineEdit())

        submit_button = QGraphicsProxyWidget()
        submit_button_widget = QPushButton("Submit")
        submit_button_widget.clicked.connect(self.submitForm)
        submit_button.setWidget(submit_button_widget)

        # Add form elements to form layout
        form_layout.addItem(name_label)
        form_layout.addItem(self.name_input)
        form_layout.addItem(email_label)
        form_layout.addItem(self.email_input)
        form_layout.addItem(submit_button)

        # Add form layout to main layout
        main_layout.addItem(form_layout)

        # Create bottom buttons layout
        bottom_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)

        # Create Clone and Delete buttons
        clone_button = QGraphicsProxyWidget()
        clone_button_widget = QPushButton("Clone")
        clone_button_widget.clicked.connect(self.cloneForm)
        clone_button.setWidget(clone_button_widget)

        delete_button = QGraphicsProxyWidget()
        delete_button_widget = QPushButton("Delete")
        delete_button_widget.clicked.connect(self.deleteForm)
        delete_button.setWidget(delete_button_widget)

        # Add buttons to bottom layout
        bottom_layout.addItem(clone_button)
        bottom_layout.addItem(delete_button)

        # Add bottom layout to main layout
        main_layout.addItem(bottom_layout)

        # Set the layout for this widget
        self.setLayout(main_layout)

    def paint(self, painter, option, widget):
        # Draw a background for the entire form
        painter.fillRect(self.boundingRect(), QBrush(QColor(240, 240, 240)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.header.boundingRect().contains(event.pos()):
            # Only start dragging if the mouse is pressed in the header area
            super().mousePressEvent(event)
        else:
            # For clicks outside the header, pass the event to children
            event.ignore()

    def mouseMoveEvent(self, event):
        if self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
            super().mouseMoveEvent(event)
            self.updateLinkLines()
        else:
            event.ignore()

    def cloneForm(self):
        from commands import CreateFormCommand

        form_width = self.boundingRect().width()
        form_height = self.boundingRect().height()

        min_gap = 20

        # Generate a random offset for a more natural spread
        random_offset_x = random.randint(min_gap, min_gap * 2)
        random_offset_y = random.randint(min_gap, min_gap * 2)

        # Determine the new position (bottom right of the parent)
        clone_pos = self.pos() + QPointF(form_width + random_offset_x, form_height + random_offset_y)

        command = CreateFormCommand(self.scene(), self, clone_pos)
        self.scene().command_invoker.execute(command)

    def adjustFormPosition(self, form):
        scene_rect = self.scene().sceneRect()
        form_rect = form.sceneBoundingRect()

        # If the form is outside the scene, adjust its position
        if not scene_rect.contains(form_rect):
            new_x = min(max(form_rect.left(), scene_rect.left()), scene_rect.right() - form_rect.width())
            new_y = min(max(form_rect.top(), scene_rect.top()), scene_rect.bottom() - form_rect.height())
            form.setPos(new_x, new_y)

    def deleteForm(self):
        # Remove this form from its parent's child_forms list
        if self.parent_form:
            self.parent_form.child_forms.remove(self)

        # Recursively delete all child forms
        for child in self.child_forms[:]:  # Create a copy of the list to iterate over
            child.deleteForm()

        # Remove the link line connecting this form to its parent
        if self.link_line:
            self.scene().removeItem(self.link_line)
            self.link_line = None

        # Remove this form from the scene
        self.scene().removeItem(self)

    def updateLinkLines(self):
        if self.link_line:
            self.link_line.updatePosition()
        for child in self.child_forms:
            child.updateLinkLines()

    def submitForm(self):
        form_data = self.gatherFormData()
        message = "Form submitted with the following data:\n\n"
        for i, data in enumerate(form_data):
            message += f"Form {i + 1}:\n"
            message += f"Name: {data['name']}\n"
            message += f"Email: {data['email']}\n\n"
        QMessageBox.information(None, "Form Submitted", message)

    def gatherFormData(self):
        data = []
        current_form = self
        while current_form:
            form_data = {
                "name": current_form.name_input.widget().text(),
                "email": current_form.email_input.widget().text(),
            }
            data.append(form_data)
            current_form = current_form.parent_form
        return reversed(data)  # Reverse to get parent data first
