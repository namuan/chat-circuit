import random
from datetime import datetime

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout, QGraphicsItem, QMessageBox, QGraphicsProxyWidget, \
    QLineEdit, QPushButton, QTextEdit

from header_widget import HeaderWidget
from link_line import LinkLine


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

        # Create chat layout
        chat_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Conversation area
        self.conversation_area = QGraphicsProxyWidget()
        conversation_widget = QTextEdit()
        conversation_widget.setReadOnly(True)
        conversation_widget.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        self.conversation_area.setWidget(conversation_widget)
        chat_layout.addItem(self.conversation_area)

        # Input area
        input_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)
        self.input_box = QGraphicsProxyWidget()
        self.input_box.setWidget(QLineEdit())
        input_layout.addItem(self.input_box)

        self.send_button = QGraphicsProxyWidget()
        send_button_widget = QPushButton("Send")
        send_button_widget.clicked.connect(self.send_message)
        self.send_button.setWidget(send_button_widget)
        input_layout.addItem(self.send_button)

        self.submit_button = QGraphicsProxyWidget()
        submit_button_widget = QPushButton("Submit")
        submit_button_widget.clicked.connect(self.submitForm)
        self.submit_button.setWidget(submit_button_widget)
        input_layout.addItem(self.submit_button)

        chat_layout.addItem(input_layout)

        # Add form layout to main layout
        main_layout.addItem(chat_layout)

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

    def send_message(self):
        input_widget = self.input_box.widget()
        message = input_widget.text()
        if message:
            self.add_message(message, is_user=True)
            input_widget.clear()
            # Simulate AI response (you'd replace this with actual AI integration)
            self.add_message("I received your message: " + message, is_user=False)

    def add_message(self, message, is_user=False):
        conversation_widget = self.conversation_area.widget()
        timestamp = datetime.now().strftime("[%d/%m/%Y %H:%M:%S]")
        prefix = "•" if is_user else "🤖"
        formatted_message = f"{timestamp} {prefix}: {message}\n"
        conversation_widget.append(formatted_message)

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
        from commands import DeleteFormCommand
        command = DeleteFormCommand(self)
        self.scene().command_invoker.execute(command)

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
            message += f"Context: {data['context']}\n"
        QMessageBox.information(None, "Form Submitted", message)

    def gatherFormData(self):
        data = []
        current_form = self
        while current_form:
            form_data = {
                "context": current_form.conversation_area.widget().toPlainText(),
            }
            data.append(form_data)
            current_form = current_form.parent_form
        return reversed(data)  # Reverse to get parent data first

    def to_dict(self):
        return {
            'pos_x': self.pos().x(),
            'pos_y': self.pos().y(),
            'name': self.name_input.widget().text(),
            'email': self.email_input.widget().text(),
            'children': [child.to_dict() for child in self.child_forms]
        }

    @classmethod
    def from_dict(cls, data, scene, parent=None):
        form = cls(parent)
        form.setPos(QPointF(data['pos_x'], data['pos_y']))
        form.name_input.widget().setText(data['name'])
        form.email_input.widget().setText(data['email'])
        scene.addItem(form)

        for child_data in data['children']:
            child = cls.from_dict(child_data, scene, form)
            form.child_forms.append(child)
            link_line = LinkLine(form, child)
            scene.addItem(link_line)
            child.link_line = link_line

        return form
