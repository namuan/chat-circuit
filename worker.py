from PyQt6.QtCore import QRunnable, pyqtSignal, QObject, QEventLoop

from network_manager import NetworkManager


class WorkerSignals(QObject):
    update = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)


class Worker(QRunnable):
    def __init__(self, model, system_message, messages):
        super().__init__()
        self.model = model
        self.messages = messages
        self.system_message = system_message or "You are a helpful assistant."
        self.signals = WorkerSignals()

    def run(self):
        network_manager = NetworkManager()
        network_manager.data_received.connect(self.signals.update.emit)
        network_manager.finished.connect(self.signals.finished.emit)
        network_manager.error.connect(self.signals.error.emit)

        network_manager.chat_completion_request(self.model, self.messages, self.system_message)

        loop = QEventLoop()
        network_manager.finished.connect(loop.quit)
        loop.exec()
