from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QListWidget)

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

    def remove_word(self):
        selected = self.list_widget.currentItem()
        if selected:
            word = selected.text()
            words = self.config_manager.get("dictionary", [])
            if word in words:
                words.remove(word)
                self.config_manager.set("dictionary", words)
                self.load_words()
