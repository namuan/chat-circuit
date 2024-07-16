# state_manager.py

from PyQt6.QtCore import QSettings


class StateManager:
    def __init__(self, company, application):
        self.settings = QSettings(company, application)

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
