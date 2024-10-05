from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from app import MainWindow


@pytest.fixture(scope="session")
def app():
    """Creates a QApplication instance for all tests."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app
    # No need to quit the QApplication after tests


@pytest.fixture
def main_window(qtbot):
    """Creates an instance of MainWindow and adds it to qtbot."""
    window = MainWindow(auto_load_state=False)
    window.load_from_file(Path.cwd() / "tests" / "test_example.json")
    window.showMaximized()
    window.show()
    qtbot.addWidget(window)
    return window
