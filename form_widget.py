import random
from collections import deque

from PyQt6.QtCore import QPointF, Qt, QThreadPool, QTimer
from PyQt6.QtGui import QBrush, QColor, QIcon
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLinearLayout,
    QGraphicsProxyWidget,
    QGraphicsWidget,
    QLineEdit,
    QSizePolicy,
    QTextEdit,
    QGraphicsRectItem,
)

from buttons_bar import add_buttons
from header_widget import HeaderWidget
from link_line import LinkLine
from worker import Worker

thread_pool = QThreadPool()
active_workers = 0


def create_svg_icon(file_path):
    icon = QIcon(file_path)
    return icon


class FormWidget(QGraphicsWidget):
    def __init__(self, parent=None, model=None):
        super().__init__()
        # LLM
        self.model = model
        self.system_message = "You are a helpful assistant."

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.parent_form = parent
        self.child_forms = []
        self.link_line = None

        # Re-Run all form nodes
        self.worker = None
        self.form_chain = deque()

        # Create main layout
        main_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Create and add header
        self.header = HeaderWidget(self.model)
        self.header.model_changed.connect(self.on_model_changed)
        self.header.setZValue(1)
        main_layout.addItem(self.header)
        self.header.update_model_name()

        # Create chat layout
        chat_layout = QGraphicsLinearLayout(Qt.Orientation.Vertical)

        # Conversation area
        self.conversation_area = QGraphicsProxyWidget()
        conversation_widget = QTextEdit()
        conversation_widget.setReadOnly(True)
        conversation_widget.setStyleSheet(
            "background-color: white; border: 1px solid #ccc;"
        )
        self.conversation_area.setWidget(conversation_widget)
        chat_layout.addItem(self.conversation_area)

        # Input box
        self.input_box = QGraphicsProxyWidget()
        self.input_line_edit = QLineEdit()
        self.input_line_edit.setStyleSheet(
            "background-color: white;" "border: 1px solid #ccc;" "padding: 1;"
        )
        self.input_line_edit.setPlaceholderText("Prompt (and press enter)")
        self.input_line_edit.setMinimumHeight(30)  # Increase minimum height
        self.input_line_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.input_line_edit.returnPressed.connect(self.submitForm)
        self.input_box.setWidget(self.input_line_edit)
        self.input_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        chat_layout.addItem(self.input_box)

        # Add form layout to main layout
        main_layout.addItem(chat_layout)

        # Create bottom buttons layout
        bottom_layout = add_buttons(self)

        # Add bottom layout to main layout
        main_layout.addItem(bottom_layout)

        # Set the layout for this widget
        QTimer.singleShot(0, self.setFocusToInput)

        self.background_item = QGraphicsRectItem(self.boundingRect(), self)
        self.background_item.setBrush(QBrush(QColor(240, 240, 240)))
        self.background_item.setZValue(-1)  # Ensure it's behind other items

        self.highlight_color = QColor(255, 165, 0, 150)  # Orange with alpha 150
        self.original_color = QColor(240, 240, 240)  # Light gray

        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.timeout.connect(self.remove_highlight)

        self.setLayout(main_layout)

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

    def setFocusToInput(self):
        self.input_line_edit.setFocus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_item.setRect(self.boundingRect())

    def mousePressEvent(self, event):
        self.setFocus()
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.header.boundingRect().contains(event.pos())
        ):
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

    def generateFollowUpQuestions(self):
        # Gather the current conversation context
        context_data = []
        for i, data in enumerate(self.gatherFormData()):
            context = data["context"]
            if context:
                message = dict(role="user", content=context)
                context_data.append(message)

        # Construct the prompt for generating follow-up questions
        prompt = (
            "Based on the conversation above,"
            "please generate 3 follow-up questions."
            "Keep them concise and relevant to the topic."
            "Just list the 3 questions without any other text."
            "Do not prefix the questions with a number."
        )
        context_data.append(dict(role="user", content=prompt))

        # Create a new worker to handle the LLM request
        self.worker = Worker(self.model, self.system_message, context_data)
        self.worker.signals.update.connect(self.handle_follow_up_questions)
        self.worker.signals.finished.connect(self.handle_finished)
        self.worker.signals.error.connect(self.handle_error)

        self.highlight_hierarchy()
        thread_pool.start(self.worker)
        self.start_processing()

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
                    from commands import CreateFormCommand

                    command = CreateFormCommand(self.scene(), self, new_pos, self.model)
                    self.scene().command_invoker.execute(command)
                    new_form = command.created_form
                    new_form.input_box.widget().setText(question)
        except Exception as e:
            self.handle_error(f"Error parsing follow-up questions: {str(e)}")

    def cloneBranch(self):
        from commands import CloneBranchCommand

        command = CloneBranchCommand(self.scene(), self)
        self.scene().command_invoker.execute(command)

    def cloneForm(self):
        from commands import CreateFormCommand

        form_width = self.boundingRect().width()
        form_height = self.boundingRect().height()

        min_gap = 20

        # Generate a random offset for a more natural spread
        random_offset_x = random.randint(min_gap, min_gap * 2)
        random_offset_y = random.randint(min_gap, min_gap * 2)

        # Determine the new position (bottom right of the parent)
        clone_pos = self.pos() + QPointF(
            form_width + random_offset_x, form_height + random_offset_y
        )

        command = CreateFormCommand(self.scene(), self, clone_pos, self.model)
        self.scene().command_invoker.execute(command)

    def deleteForm(self):
        from commands import DeleteFormCommand

        command = DeleteFormCommand(self)
        self.scene().command_invoker.execute(command)

    def updateLinkLines(self):
        if self.link_line:
            self.link_line.updatePosition()
        for child in self.child_forms:
            child.updateLinkLines()

    def allForms(self):
        self.form_chain.appendleft(self)
        current_form = self
        while current_form:
            current_form = current_form.parent_form
            if current_form:
                self.form_chain.appendleft(current_form)

    def process_next_form(self):
        try:
            form = self.form_chain.popleft()
            print(f"❓{form.input_box.widget().text().strip()}")
            form.submitForm()
            form.worker.signals.notify_child.connect(self.process_next_form)
        except IndexError:
            print("Processed all forms")

    def reRunAll(self):
        self.allForms()
        self.process_next_form()

    def submitForm(self):
        if not self.input_box.widget().text().strip():  # Check if input is not empty
            return

        form_data = self.gatherFormData()
        context_data = []
        for i, data in enumerate(form_data):
            context = data["context"]
            if context:
                message = dict(role="user", content=context)
                context_data.append(message)

        current_message = dict(role="user", content=self.input_box.widget().text())
        context_data.append(current_message)

        self.worker = Worker(self.model, self.system_message, context_data)
        self.worker.signals.update.connect(self.handle_update)
        self.worker.signals.finished.connect(self.handle_finished)
        self.worker.signals.error.connect(self.handle_error)

        self.highlight_hierarchy()
        thread_pool.start(self.worker)
        self.start_processing()

    def start_processing(self):
        global active_workers
        active_workers += 1
        self.header.start_processing()

    def stop_processing(self):
        global active_workers
        active_workers -= 1
        self.header.stop_processing()
        self.worker.signals.notify_child.emit()

    def on_model_changed(self, new_model):
        self.model = new_model

    def handle_update(self, text):
        self.update_answer(text)

    def handle_finished(self):
        self.stop_processing()

    def handle_error(self, error):
        self.stop_processing()
        self.update_answer(f"Error occurred: {error}")

    def update_answer(self, message):
        conversation_widget = self.conversation_area.widget()
        conversation_widget.setText(message)

    def gatherFormData(self):
        data = []
        current_form = self.parent_form or self
        while current_form:
            form_data = {
                "context": current_form.conversation_area.widget().toPlainText(),
            }
            data.append(form_data)
            current_form = current_form.parent_form
        return reversed(data)  # Reverse to get parent data first

    def to_dict(self):
        return {
            "pos_x": self.pos().x(),
            "pos_y": self.pos().y(),
            "input": self.input_box.widget().text(),
            "context": self.conversation_area.widget().toPlainText(),
            "children": [child.to_dict() for child in self.child_forms],
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data, scene, parent=None):
        form = cls(parent, model=data["model"])
        form.setPos(QPointF(data["pos_x"], data["pos_y"]))
        form.input_box.widget().setText(data["input"])
        form.conversation_area.widget().setPlainText(data["context"])
        if "model" in data:
            form.model = data["model"]
            form.header.update_model_name()
        scene.addItem(form)

        for child_data in data["children"]:
            child = cls.from_dict(child_data, scene, form)
            form.child_forms.append(child)
            link_line = LinkLine(form, child)
            scene.addItem(link_line)
            child.link_line = link_line

        return form
