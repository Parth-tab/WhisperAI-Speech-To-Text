import sys
import pytest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from src.gui.overlay import RecordingOverlay

# Ensure QApplication exists for tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

@patch('src.gui.overlay.QTimer')
def test_recording_overlay_logic(mock_timer):
    overlay = RecordingOverlay()
    
    assert overlay.level == 0.0
    assert overlay.target_level == 0.0
    
    overlay.update_level(0.05)
    assert overlay.target_level == min(1.0, 0.05 * 15.0)
    
    with patch.object(overlay, 'update') as mock_update, patch.object(overlay, 'isVisible', return_value=True):
        overlay.animate()
        assert overlay.level > 0.0
        mock_update.assert_called_once()
