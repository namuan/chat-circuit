import mistune

from PyQt6.QtGui import QTextDocument


class HtmlRenderer(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__()
        self.text_document = QTextDocument()

    def render(self, text):
        markdown = mistune.create_markdown(renderer=self)
        html = markdown(text)
        self.text_document.setHtml(html)
        return self.text_document
