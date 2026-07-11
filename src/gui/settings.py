from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QDoubleSpinBox)
from PySide6.QtCore import Signal

class SettingsWindow(QWidget):
    settings_saved = Signal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle("WhisperAI Settings")
        self.resize(300, 200)
        
        layout = QVBoxLayout()
        
        self.hotkey_label = QLabel("Hotkey:")
        layout.addWidget(self.hotkey_label)
        self.hotkey_input = QLineEdit(self.config_manager.get("hotkey", "<ctrl>+<alt>+w"))
        layout.addWidget(self.hotkey_input)
        
        self.vad_label = QLabel("VAD Threshold:")
        layout.addWidget(self.vad_label)
        self.vad_input = QDoubleSpinBox()
        self.vad_input.setRange(0.0, 1.0)
        self.vad_input.setSingleStep(0.1)
        self.vad_input.setValue(self.config_manager.get("vad_threshold", 0.5))
        layout.addWidget(self.vad_input)
        
        self.model_label = QLabel("Model Selection:")
        layout.addWidget(self.model_label)
        self.model_input = QComboBox()
        self.model_input.addItems(["tiny", "base", "small", "medium", "large"])
        current_model = self.config_manager.get("model_selection", "base")
        if current_model in ["tiny", "base", "small", "medium", "large"]:
            self.model_input.setCurrentText(current_model)
        layout.addWidget(self.model_input)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)

    def save_settings(self):
        new_hotkey = self.hotkey_input.text()
        new_vad = self.vad_input.value()
        new_model = self.model_input.currentText()
        
        self.config_manager.set("hotkey", new_hotkey)
        self.config_manager.set("vad_threshold", new_vad)
        self.config_manager.set("model_selection", new_model)
        
        self.settings_saved.emit({
            "hotkey": new_hotkey,
            "vad_threshold": new_vad,
            "model_selection": new_model
        })
        self.close()
