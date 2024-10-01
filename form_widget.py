import random
import re
from collections import deque

from PyQt6.QtCore import QPointF, QThreadPool, pyqtSignal, QRectF, QSizeF
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QIcon, QCursor, QPen, QFont, QAction
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLinearLayout,
    QGraphicsProxyWidget,
    QGraphicsWidget,
    QTextEdit,
    QSizePolicy,
    QGraphicsRectItem,
    QLabel,
    QWidget,
    QVBoxLayout,
    QMenu,
)

from buttons_bar import add_buttons
from header_widget import HeaderWidget
from hover_circle import HoverCircle
from link_line import LinkLine
from markdown_render import HtmlRenderer
from worker import JinaReaderWorker, LlmWorker

thread_pool = QThreadPool()
active_workers = 0


def create_svg_icon(file_path):
    icon = QIcon(file_path)
    return icon


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
            new_width = max(
                self.initial_size.width() + delta.x(), self.parentItem().minimumWidth()
            )
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
        conversation_widget = QTextEdit()
        conversation_widget.setReadOnly(True)
        conversation_widget.setAcceptRichText(True)
        conversation_widget.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: white;
                border: 1px solid #ccc;
                font-family: {self.custom_font.family()};
                font-size: {self.custom_font.pointSize()}pt;
            }}
            """
        )
        self.conversation_area.setWidget(conversation_widget)
        chat_layout.addItem(self.conversation_area)
        self.conversation_area.widget().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.conversation_area.widget().customContextMenuRequested.connect(
            self.show_context_menu
        )

        # Create a horizontal layout for emoji and input box
        input_layout = QGraphicsLinearLayout(Qt.Orientation.Horizontal)

        # Input box
        self.input_box = QGraphicsProxyWidget()
        self.input_text_edit = QTextEdit()
        self.input_text_edit.setPlaceholderText(
            "Prompt (and press Ctrl+Enter to submit)"
        )
        self.input_text_edit.setMinimumHeight(30)
        self.input_text_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.input_text_edit.textChanged.connect(self.adjustInputBoxHeight)
        self.input_box.setWidget(self.input_text_edit)
        self.input_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Connect the key press event
        self.input_text_edit.installEventFilter(self)

        input_layout.addItem(self.input_box)

        # Create and add emoji label
        self.emoji_label = self.create_emoji_label()
        self.emoji_container = QWidget()
        emoji_container_layout = QVBoxLayout(self.emoji_container)
        emoji_container_layout.addWidget(self.emoji_label)
        emoji_container_layout.setContentsMargins(0, 0, 0, 0)
        self.emoji_proxy = QGraphicsProxyWidget()
        self.emoji_proxy.setWidget(self.emoji_container)
        input_layout.addItem(self.emoji_proxy)

        chat_layout.addItem(input_layout)

        # Add form layout to main layout
        self.main_layout.addItem(chat_layout)

        # Create bottom buttons layout
        bottom_layout = add_buttons(self)

        # Add bottom layout to main layout
        self.main_layout.addItem(bottom_layout)

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

        self.setLayout(self.main_layout)

        self.resize_handle = ResizeHandle(self)
        self.resize_handle.resize_signal.connect(self.resize_widget)
        self.update_resize_handle()

        self.circle_item = HoverCircle(self)
        self.circle_item.setZValue(2)

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
            # Get the scene and create a new position for the new form
            scene = self.scene()
            new_pos = self.pos() + QPointF(500, 200)  # Offset from current form

            # Create a new form using the existing CreateFormCommand
            from commands import CreateFormCommand

            command = CreateFormCommand(scene, self, new_pos, self.model)
            scene.command_invoker.execute(command)
            new_form = command.created_form
            new_form.input_box.widget().setPlainText(f"Explain {selected_text}")

    def create_emoji_label(self):
        emoji_label = QLabel("❓")  # You can change this to any emoji you prefer
        emoji_label.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                background-color: lightgray;
            }
        """
        )
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        emoji_label.setCursor(
            Qt.CursorShape.PointingHandCursor
        )  # Change cursor on hover
        emoji_label.mousePressEvent = self.emoji_label_clicked  # Connect click event
        return emoji_label

    def emoji_label_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.submit_form()

    def resize_widget(self, new_size: QPointF):
        new_width = max(new_size.x(), self.minimumWidth())
        new_height = max(new_size.y(), self.minimumHeight())
        self.prepareGeometryChange()
        self.resize(new_width, new_height)
        self.update_resize_handle()

    def update_resize_handle(self):
        if self.resize_handle:
            self.resize_handle.setPos(
                self.rect().width() - 10, self.rect().height() - 10
            )

    def eventFilter(self, obj, event):
        if obj == self.input_text_edit and event.type() == event.Type.KeyPress:
            if (
                event.key() == Qt.Key.Key_Return
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self.submit_form()
                return True
        return super().eventFilter(obj, event)

    def adjustInputBoxHeight(self):
        document = self.input_text_edit.document()
        new_height = max(
            document.size().height() + 10, 30
        )  # Add some padding and set minimum height
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

    def setFocusToInput(self):
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
        if (
            self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            and not self.circle_item.isUnderMouse()
        ):
            super().mouseMoveEvent(event)
            self.update_link_lines()
        else:
            event.ignore()

    def generate_follow_up_questions(self):
        # Gather the current conversation context
        context_data = []
        for i, data in enumerate(self.gather_form_data()):
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
        self.worker = LlmWorker(self.model, self.system_message, context_data)
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
                    new_form.input_box.widget().setPlainText(question)
        except Exception as e:
            self.handle_error(f"Error parsing follow-up questions: {str(e)}")

    def clone_branch(self):
        from commands import CloneBranchCommand

        command = CloneBranchCommand(self.scene(), self)
        self.scene().command_invoker.execute(command)

    def clone_form(self):
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

    def delete_form(self):
        from commands import DeleteFormCommand

        command = DeleteFormCommand(self)
        self.scene().command_invoker.execute(command)

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
            print(f"❓{form.input_box.widget().toPlainText().strip()}")
            form.submit_form()
            form.worker.signals.notify_child.connect(self.process_next_form)
        except IndexError:
            print("Processed all forms")

    def re_run_all(self):
        self.all_forms()
        self.process_next_form()

    def submit_form(self):
        input_text = self.input_box.widget().toPlainText().strip()
        if not input_text:
            return

        # Check if the input is a URL
        url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
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
        QThreadPool.globalInstance().start(self.jina_worker)
        self.start_processing()

    def handle_jina_reader_content(self, content):
        self.stop_processing()
        self.update_answer(content)

    def process_llm_request(self, input_text):
        form_data = self.gather_form_data()
        context_data = []
        for i, data in enumerate(form_data):
            context = data["context"]
            if context:
                message = dict(role="user", content=context)
                context_data.append(message)

        current_message = dict(role="user", content=input_text)
        context_data.append(current_message)

        self.llm_worker = LlmWorker(self.model, self.system_message, context_data)
        self.llm_worker.signals.update.connect(self.handle_update)
        self.llm_worker.signals.finished.connect(self.handle_finished)
        self.llm_worker.signals.error.connect(self.handle_error)

        self.highlight_hierarchy()
        QThreadPool.globalInstance().start(self.llm_worker)
        self.start_processing()

    def start_processing(self):
        global active_workers
        active_workers += 1
        self.header.start_processing()

    def stop_processing(self):
        global active_workers
        active_workers -= 1
        self.header.stop_processing()
        if self.llm_worker:
            self.llm_worker.signals.notify_child.emit()

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
        self.markdown_content = message
        conversation_widget = self.conversation_area.widget()
        renderer = HtmlRenderer()
        conversation_widget.setDocument(renderer.render(self.markdown_content))

    def gather_form_data(self):
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
            "width": self.size().width(),
            "height": self.size().height(),
            "input": self.input_box.widget().toPlainText(),
            "context": self.markdown_content,
            "children": [child.to_dict() for child in self.child_forms],
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data, scene, parent=None):
        form = cls(parent, model=data["model"])
        form.setPos(QPointF(data["pos_x"], data["pos_y"]))

        # Use default values if width and height are not in the data
        default_width = 300  # Set an appropriate default width
        default_height = 200  # Set an appropriate default height
        width = data.get("width", default_width)
        height = data.get("height", default_height)
        form.resize(width, height)

        form.input_box.widget().setPlainText(data["input"])
        form.markdown_content = data["context"]
        form.update_answer(form.markdown_content)
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
