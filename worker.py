import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
from litellm import completion


class LlmWorkerSignals(QObject):
    update = pyqtSignal(str)
    finished = pyqtSignal()
    notify_child = pyqtSignal()
    error = pyqtSignal(str)


class LlmWorker(QRunnable):
    def __init__(self, model, system_message, messages):
        super().__init__()
        self.model = model
        self.messages = messages
        self.system_message = system_message or "You are a helpful assistant."
        self.signals = LlmWorkerSignals()

    def run(self):
        try:
            formatted_messages = []
            if self.system_message:
                formatted_messages.append(
                    {"role": "system", "content": self.system_message}
                )
            formatted_messages.extend(self.messages)

            response = completion(
                model=f"{self.model}",
                messages=formatted_messages,
                api_base="http://localhost:11434",
            )

            content = response.choices[0].message.content
            self.signals.update.emit(content)
            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.notify_child.emit()


class JinaReaderWorkerSignals(QObject):
    result = pyqtSignal(str)
    error = pyqtSignal(str)


class JinaReaderWorker(QRunnable):
    def __init__(self, url, jina_api_key):
        super().__init__()
        self.url = url
        self.jina_api_key = jina_api_key
        self.signals = JinaReaderWorkerSignals()

    def run(self):
        try:
            jina_url = f"https://r.jina.ai/{self.url}"
            headers = {"Authorization": f"Bearer {self.jina_api_key}"}
            response = requests.get(jina_url, headers=headers)
            response.raise_for_status()

            content = response.text
            self.signals.result.emit(content)
        except Exception as e:
            self.signals.error.emit(str(e))
