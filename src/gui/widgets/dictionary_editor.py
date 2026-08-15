import json
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QComboBox,
    QLabel,
)
from src.utils.paths import get_asset_path

logger = logging.getLogger("whisperai")


class DictionaryEditor(QWidget):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.load_words()
        layout.addWidget(self.list_widget)

        input_layout = QHBoxLayout()
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Enter a word or acronym...")
        input_layout.addWidget(self.word_input)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_word)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        # 1-Click Industry Pre-Packs
        pack_layout = QHBoxLayout()
        self.pack_dropdown = QComboBox()
        self.pack_dropdown.addItems([
            "Select Industry Pack...",
            "Medical",
            "Legal",
            "Financial",
            "DevOps",
        ])
        pack_layout.addWidget(self.pack_dropdown)

        self.load_pack_button = QPushButton("Load 1-Click Pack")
        self.load_pack_button.clicked.connect(self.load_industry_pack)
        pack_layout.addWidget(self.load_pack_button)
        layout.addLayout(pack_layout)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_word)
        layout.addWidget(self.remove_button)

    def load_words(self):
        self.list_widget.clear()
        words = self.config_manager.get("dictionary", [])
        self.list_widget.addItems(words)

    def add_word(self):
        word = self.word_input.text().strip()
        if word:
            words = self.config_manager.get("dictionary", [])
            if word not in words:
                words.append(word)
                self.config_manager.set("dictionary", words)
                self.load_words()
                self.word_input.clear()

    def load_industry_pack(self):
        pack_name = self.pack_dropdown.currentText().strip().lower()
        if pack_name == "select industry pack...":
            return

        rel_path = f"resources/industry_packs/{pack_name}.json"
        pack_file = Path(get_asset_path(rel_path))
        if not pack_file.exists():
            pack_file = Path(__file__).resolve().parent.parent.parent.parent / "resources" / "industry_packs" / f"{pack_name}.json"

        try:
            with open(pack_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            pack_terms = data.get("terms", [])
            if isinstance(pack_terms, dict):
                pack_terms = list(pack_terms.keys())

            words = self.config_manager.get("dictionary", [])
            added_count = 0
            for term in pack_terms:
                if term not in words:
                    words.append(term)
                    added_count += 1

            self.config_manager.set("dictionary", words)
            self.load_words()
            logger.info(f"[DictionaryEditor] Loaded {added_count} terms from {pack_name} pre-pack.")
        except Exception as e:
            logger.error(f"[DictionaryEditor] Failed to load pack {pack_name}: {e}")

    def remove_word(self):
        selected = self.list_widget.currentItem()
        if selected:
            word = selected.text()
            words = self.config_manager.get("dictionary", [])
            if word in words:
                words.remove(word)
                self.config_manager.set("dictionary", words)
                self.load_words()
