from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Jina API Key input
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Jina API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        layout.addLayout(api_key_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Connect buttons
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def get_jina_api_key(self):
        return self.api_key_input.text()

    def set_jina_api_key(self, jina_api_key):
        self.api_key_input.setText(jina_api_key)
