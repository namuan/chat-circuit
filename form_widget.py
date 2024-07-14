import random

from PyQt6.QtCore import Qt, QPointF, QThreadPool, QTimer
from PyQt6.QtGui import QBrush, QColor, QKeyEvent
from PyQt6.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout, QGraphicsItem, QGraphicsProxyWidget, \
    QLineEdit, QPushButton, QTextEdit, QSizePolicy

from header_widget import HeaderWidget
from link_line import LinkLine
from worker import Worker

thread_pool = QThreadPool()
active_workers = 0


class FormWidget(QGraphicsWidget):
    def __init__(self, parent=None):
        super().__init__()
        # LLM
        self.model = "openchat"
        self.system_message = "You are a helpful assistant."

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.parent_form = parent
        self.child_forms = []
        self.link_line = None

        # Create main layout
        main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Create and add header
        self.header = HeaderWidget(self.model)
        main_layout.addItem(self.header)
        self.header.update_model_name()

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

        # Input box
        self.input_box = QGraphicsProxyWidget()
        self.input_line_edit = QLineEdit()
        self.input_line_edit.setMinimumHeight(30)  # Increase minimum height
        self.input_line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_line_edit.returnPressed.connect(self.submitForm)
        self.input_box.setWidget(self.input_line_edit)
        self.input_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        input_layout.addItem(self.input_box)

        # Submit button
        self.submit_button = QGraphicsProxyWidget()
        submit_button_widget = QPushButton("Submit")
        submit_button_widget.clicked.connect(self.submitForm)
        self.submit_button.setWidget(submit_button_widget)
        input_layout.addItem(self.submit_button)

        # Set stretch factors to make input box wider than button
        input_layout.setStretchFactor(self.input_box, 3)
        input_layout.setStretchFactor(self.submit_button, 1)

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
        bottom_layout.addItem(clone_button)

        delete_button = QGraphicsProxyWidget()
        delete_button_widget = QPushButton("Delete")
        delete_button_widget.clicked.connect(self.deleteForm)
        delete_button.setWidget(delete_button_widget)
        bottom_layout.addItem(delete_button)

        # Add bottom layout to main layout
        main_layout.addItem(bottom_layout)

        # Set the layout for this widget
        QTimer.singleShot(0, self.setFocusToInput)

        self.setLayout(main_layout)

    def setFocusToInput(self):
        # This method will be called after the widget is fully initialized
        self.input_line_edit.setFocus()

    def paint(self, painter, option, widget):
        # Draw a background for the entire form
        painter.fillRect(self.boundingRect(), QBrush(QColor(240, 240, 240)))

    def keyPressEvent(self, event: QKeyEvent):
        # Check for Command+C (Clone)
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.cloneForm()
            return

        # Check for Command+D (Delete)
        if event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.deleteForm()
            return

        # If the event wasn't handled, pass it to the parent class
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.setFocus()
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
        if not self.input_box.widget().text().strip():  # Check if input is not empty
            return

        global active_workers
        form_data = self.gatherFormData()
        context_data = []
        for i, data in enumerate(form_data):
            context = data['context']
            if context:
                message = dict(
                    role="user",
                    content=context
                )
                context_data.append(message)

        current_message = dict(
            role="user",
            content=self.input_box.widget().text()
        )
        context_data.append(current_message)

        worker = Worker(self.model, self.system_message, context_data)
        worker.signals.update.connect(self.handle_update)
        worker.signals.finished.connect(self.handle_finished)
        worker.signals.error.connect(self.handle_error)

        thread_pool.start(worker)
        active_workers += 1
        self.start_processing_indicator()

    def start_processing_indicator(self):
        self.header.start_processing()
        self.submit_button.widget().setEnabled(False)
        self.submit_button.widget().setText("...")

    def stop_processing_indicator(self):
        self.header.stop_processing()
        self.submit_button.widget().setEnabled(True)
        self.submit_button.widget().setText("Submit")

    def handle_update(self, text):
        self.stop_processing_indicator()
        self.update_answer(text)

    def handle_finished(self):
        global active_workers
        active_workers -= 1
        self.stop_processing_indicator()

    def handle_error(self, error):
        global active_workers
        active_workers -= 1
        self.stop_processing_indicator()
        self.update_answer(f"Error occurred: {error}")

    def update_answer(self, message):
        conversation_widget = self.conversation_area.widget()
        conversation_widget.append(message)

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
            'input': self.input_box.widget().text(),
            'context': self.conversation_area.widget().toPlainText(),
            'children': [child.to_dict() for child in self.child_forms],
            'model': self.model,
        }

    @classmethod
    def from_dict(cls, data, scene, parent=None):
        form = cls(parent)
        form.setPos(QPointF(data['pos_x'], data['pos_y']))
        form.input_box.widget().setText(data['input'])
        form.conversation_area.widget().setPlainText(data['context'])
        if 'model' in data:
            form.model = data['model']
            form.header.update_model_name()
        scene.addItem(form)

        for child_data in data['children']:
            child = cls.from_dict(child_data, scene, form)
            form.child_forms.append(child)
            link_line = LinkLine(form, child)
            scene.addItem(link_line)
            child.link_line = link_line

        return form
