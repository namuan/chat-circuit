from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
from litellm import completion


class WorkerSignals(QObject):
    update = pyqtSignal(str)
    finished = pyqtSignal()
    notify_child = pyqtSignal()
    error = pyqtSignal(str)


class Worker(QRunnable):
    def __init__(self, model, system_message, messages):
        super().__init__()
        self.model = model
        self.messages = messages
        self.system_message = system_message or "You are a helpful assistant."
        self.signals = WorkerSignals()

    def run(self):
        try:
            # Prepare the messages
            formatted_messages = []
            if self.system_message:
                formatted_messages.append(
                    {"role": "system", "content": self.system_message}
                )
            formatted_messages.extend(self.messages)

            # Make the API call using litellm
            response = completion(
                model=f"{self.model}",
                messages=formatted_messages,
                api_base="http://localhost:11434",
            )

            # Extract the content from the response
            content = response.choices[0].message.content

            # Emit the update signal with the full response
            self.signals.update.emit(content)

            # Emit the finished signal
            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.notify_child.emit()
