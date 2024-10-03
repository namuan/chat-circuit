import json
import os
from pathlib import Path

from PyQt6.QtCore import QEvent
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from app import CreateFormCommand
from app import FormWidget
from app import JsonCanvasExporter


def interact(qtbot):
    qtbot.stopForInteraction()


def test_main_window_opens(main_window, qtbot):
    """Checks if the main window opens with the correct title."""
    assert main_window.windowTitle().startswith("Chat Circuit") is True
    assert main_window.isVisible()


def test_create_new_form_via_shortcut(main_window, qtbot):
    qtbot.waitForWindowShown(main_window)
    main_window.load_from_file(Path.cwd() / "tests" / "test_example.json")

    """Checks if a new form is created when Ctrl+N is pressed."""
    initial_form_count = len(
        [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
    )

    key_event = QKeyEvent(
        QEvent.Type.KeyPress, Qt.Key.Key_I, Qt.KeyboardModifier.ControlModifier, "I"
    )
    main_window.scene.keyPressEvent(key_event)

    # Allow time for event processing
    qtbot.wait(200)

    new_form_count = len(
        [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
    )
    assert new_form_count == initial_form_count + 1


def test_undo_redo_create_form(main_window, qtbot):
    """Tests Undo and Redo functionality for creating a form."""
    initial_form_count = len(
        [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
    )

    # Create a new form
    command = CreateFormCommand(main_window.scene)
    main_window.scene.command_invoker.execute(command)
    qtbot.wait(100)
    assert (
        len(
            [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
        )
        == initial_form_count + 1
    )

    # Undo creation
    main_window.undo()
    qtbot.wait(100)
    assert (
        len(
            [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
        )
        == initial_form_count
    )

    # Redo creation
    main_window.redo()
    qtbot.wait(100)
    assert (
        len(
            [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
        )
        == initial_form_count + 1
    )


def test_save_and_load_state(tmp_path, main_window, qtbot):
    """Checks if the application state is saved and loaded correctly."""
    # Create multiple forms
    for _ in range(3):
        command = CreateFormCommand(main_window.scene)
        main_window.scene.command_invoker.execute(command)
        qtbot.wait(100)

    form_count_before = len(
        [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
    )
    assert form_count_before == 3

    # Save state to a temporary file
    save_file = tmp_path / "test_save.json"
    main_window.state_manager.save_last_file(str(save_file))
    main_window.save_state()

    # Clear the scene
    main_window.scene.clear()
    qtbot.wait(100)
    form_count_cleared = len(
        [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
    )
    assert form_count_cleared == 0

    # Load state from the file
    main_window.load_from_file(str(save_file))
    qtbot.wait(100)
    form_count_loaded = len(
        [item for item in main_window.scene.items() if isinstance(item, FormWidget)]
    )
    assert form_count_loaded == 3


def test_export_to_json_canvas(tmp_path, main_window, qtbot):
    """Ensures that exporting the canvas to a JSON file works correctly."""
    # Create multiple forms
    for _ in range(2):
        command = CreateFormCommand(main_window.scene)
        main_window.scene.command_invoker.execute(command)
        qtbot.wait(100)

    # Export the canvas
    export_file = tmp_path / "export.canvas"
    exporter = JsonCanvasExporter(main_window.scene)
    exporter.export(str(export_file))

    # Check if the file was created
    assert os.path.exists(export_file)

    # Verify the contents of the file
    with open(export_file) as f:
        data = json.load(f)

    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 2


# tests/test_llm_worker.py


def test_llm_worker_handle_update(main_window, qtbot, mocker):
    """Ensures that LLM responses are handled and displayed correctly."""
    # Mock the 'completion' function from litellm
    mock_completion = mocker.patch("app.completion")
    mock_response = mocker.Mock()
    mock_response.choices = [
        mocker.Mock(message=mocker.Mock(content="Test LLM response"))
    ]
    mock_completion.return_value = mock_response

    # Create a new form
    command = CreateFormCommand(main_window.scene)
    main_window.scene.command_invoker.execute(command)
    qtbot.wait(100)
    new_form = [
        item for item in main_window.scene.items() if isinstance(item, FormWidget)
    ][-1]

    # Enter text and submit the form
    qtbot.keyClicks(new_form.input_box.widget(), "Hello, LLM!")
    qtbot.mouseClick(new_form.emoji_label, Qt.MouseButton.LeftButton)

    # Allow time for the worker to process
    qtbot.wait(500)

    # Check if the response is displayed correctly
    assert (
        new_form.conversation_area.widget()
        .toPlainText()
        .startswith("Test LLM response")
        is True
    )
