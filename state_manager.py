# state_manager.py

from PyQt6.QtCore import QSettings
import keyring


class StateManager:
    def __init__(self, company, application):
        self.settings = QSettings(company, application)
        self.keyring_service = f"{company}-{application}"

    def save_window_state(self, window):
        self.settings.setValue("window_geometry", window.saveGeometry())
        self.settings.setValue("window_state", window.saveState())

    def restore_window_state(self, window):
        geometry = self.settings.value("window_geometry")
        state = self.settings.value("window_state")

        if geometry and state:
            window.restoreGeometry(geometry)
            window.restoreState(state)
            return True
        return False

    def save_last_file(self, file_path):
        self.settings.setValue("last_file", file_path)

    def get_last_file(self):
        return self.settings.value("last_file")

    def clear_settings(self):
        self.settings.clear()

    def save_jina_api_key(self, jina_api_key):
        keyring.set_password(self.keyring_service, "jina_api_key", jina_api_key)

    def get_jina_api_key(self):
        return keyring.get_password(self.keyring_service, "jina_api_key") or ""

    def clear_jina_api_key(self):
        keyring.delete_password(self.keyring_service, "jina_api_key")
