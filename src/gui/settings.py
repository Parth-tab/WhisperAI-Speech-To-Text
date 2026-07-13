from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QDoubleSpinBox, QTabWidget)
from PySide6.QtCore import Signal
from src.gui.widgets.dictionary_editor import DictionaryEditor
from src.gui.widgets.snippet_editor import SnippetEditor

class SettingsWindow(QWidget):
    settings_saved = Signal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle("WhisperAI Settings")
        self.resize(500, 400)
        
        main_layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        
        # --- General Tab ---
        self.general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        self.hotkey_label = QLabel("Hotkey:")
        general_layout.addWidget(self.hotkey_label)
        self.hotkey_input = QLineEdit(self.config_manager.get("hotkey", "<ctrl>+<alt>+w"))
        general_layout.addWidget(self.hotkey_input)
        
        self.vad_label = QLabel("VAD Threshold:")
        general_layout.addWidget(self.vad_label)
        self.vad_input = QDoubleSpinBox()
        self.vad_input.setRange(0.0, 1.0)
        self.vad_input.setSingleStep(0.1)
        self.vad_input.setValue(self.config_manager.get("vad_threshold", 0.5))
        general_layout.addWidget(self.vad_input)
        
        self.model_label = QLabel("Model Selection:")
        general_layout.addWidget(self.model_label)
        self.model_input = QComboBox()
        self.model_input.addItems(["tiny", "base", "small", "medium", "large"])
        current_model = self.config_manager.get("model_selection", "base")
        if current_model in ["tiny", "base", "small", "medium", "large"]:
            self.model_input.setCurrentText(current_model)
        general_layout.addWidget(self.model_input)
        
        from PySide6.QtWidgets import QCheckBox
        self.whisper_mode_label = QLabel("Whisper Mode:")
        general_layout.addWidget(self.whisper_mode_label)
        self.whisper_mode_input = QCheckBox("Enable highly sensitive low-volume dictation")
        self.whisper_mode_input.setChecked(self.config_manager.get("whisper_mode", False))
        general_layout.addWidget(self.whisper_mode_input)
        
        general_layout.addStretch()
        self.general_tab.setLayout(general_layout)
        self.tabs.addTab(self.general_tab, "General")
        
        # --- Dictionary Tab ---
        self.dictionary_tab = DictionaryEditor(self.config_manager)
        self.tabs.addTab(self.dictionary_tab, "Dictionary")
        
        # --- Snippets Tab ---
        self.snippets_tab = SnippetEditor(self.config_manager)
        self.tabs.addTab(self.snippets_tab, "Snippets")
        
        main_layout.addWidget(self.tabs)
        
        self.save_button = QPushButton("Save & Close")
        self.save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(self.save_button)
        
        self.setLayout(main_layout)

    def save_settings(self):
        new_hotkey = self.hotkey_input.text()
        new_vad = self.vad_input.value()
        new_model = self.model_input.currentText()
        new_whisper_mode = self.whisper_mode_input.isChecked()
        
        self.config_manager.set("hotkey", new_hotkey)
        self.config_manager.set("vad_threshold", new_vad)
        self.config_manager.set("model_selection", new_model)
        self.config_manager.set("whisper_mode", new_whisper_mode)
        
        self.settings_saved.emit({
            "hotkey": new_hotkey,
            "vad_threshold": new_vad,
            "model_selection": new_model,
            "whisper_mode": new_whisper_mode
        })
        self.close()
