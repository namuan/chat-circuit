import json

from PyQt6.QtCore import QByteArray, QObject, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest


class NetworkManager(QObject):
    data_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()

    def chat_completion_request(self, model, messages, system_message=None):
        url = "http://localhost:11434/v1/chat/completions"
        headers = {"Content-Type": "application/json"}

        # Prepare the messages
        formatted_messages = []
        if system_message:
            formatted_messages.append({"role": "system", "content": system_message})
        formatted_messages.extend(messages)

        data = {"model": model, "messages": formatted_messages}

        # Convert data to JSON
        json_data = json.dumps(data)

        print(">>>" + json_data)

        # Create request
        request = QNetworkRequest(QUrl(url))

        # Set headers
        for key, value in headers.items():
            request.setRawHeader(key.encode(), value.encode())

        # Send POST request
        reply = self.manager.post(request, QByteArray(json_data.encode()))

        reply.readyRead.connect(lambda: self.process_data(reply))
        reply.finished.connect(self.handle_finished)
        reply.errorOccurred.connect(self.handle_error)

    def process_data(self, reply):
        data = reply.readAll().data().decode("utf-8")
        print("<<<" + data)
        try:
            json_data = json.loads(data)
            content = json_data["choices"][0]["message"]["content"]
            self.data_received.emit(content)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self.error.emit(f"Error processing response: {str(e)}")

    def handle_finished(self):
        self.finished.emit()

    def handle_error(self):
        reply = self.sender()
        self.error.emit(f"Error: {reply.errorString()}")
