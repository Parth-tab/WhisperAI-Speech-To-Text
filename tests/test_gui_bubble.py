import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.gui.flow_bubble import FlowBubble, BubbleState, WaveformWidget, SpinnerWidget
from src.config.manager import ConfigManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_waveform_widget_levels(qapp):
    widget = WaveformWidget()
    assert len(widget.levels) == 7
    widget.update_level(0.8)
    assert any(lvl > 0.0 for lvl in widget.levels)


def test_spinner_widget_animation(qapp):
    spinner = SpinnerWidget()
    assert spinner.angle == 0
    spinner.rotate()
    assert spinner.angle == 15
    assert spinner.timer.isActive()


@patch("src.gui.flow_bubble.get_active_caret_coordinates", return_value=(200, 300))
def test_flow_bubble_state_transitions(mock_caret, qapp):
    cfg = ConfigManager()
    bubble = FlowBubble(cfg)
    
    # Initial state
    assert bubble.state == BubbleState.IDLE
    
    # Transition to RECORDING
    bubble.set_state(BubbleState.RECORDING)
    assert bubble.state == BubbleState.RECORDING
    assert bubble.waveform.isVisible()
    
    # Transition to PROCESSING
    bubble.set_state(BubbleState.PROCESSING)
    assert bubble.state == BubbleState.PROCESSING
    assert bubble.spinner.isVisible()
    
    # Back to IDLE
    bubble.set_state(BubbleState.IDLE)
    assert bubble.state == BubbleState.IDLE
    bubble.close()
