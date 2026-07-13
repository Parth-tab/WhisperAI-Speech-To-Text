from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)

class SnippetEditor(QWidget):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        layout = QVBoxLayout(self)
        
        self.table_widget = QTableWidget(0, 2)
        self.table_widget.setHorizontalHeaderLabels(["Trigger Phrase", "Expansion Text"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_snippets()
        layout.addWidget(self.table_widget)
        
        input_layout = QHBoxLayout()
        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("Trigger phrase...")
        input_layout.addWidget(self.trigger_input)
        
        self.expansion_input = QLineEdit()
        self.expansion_input.setPlaceholderText("Expansion text...")
        input_layout.addWidget(self.expansion_input)
        
        self.add_button = QPushButton("Add / Update")
        self.add_button.clicked.connect(self.add_snippet)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_snippet)
        layout.addWidget(self.remove_button)

    def load_snippets(self):
        self.table_widget.setRowCount(0)
        snippets = self.config_manager.get("snippets", {})
        for trigger, expansion in snippets.items():
            row_pos = self.table_widget.rowCount()
            self.table_widget.insertRow(row_pos)
            self.table_widget.setItem(row_pos, 0, QTableWidgetItem(trigger))
            self.table_widget.setItem(row_pos, 1, QTableWidgetItem(expansion))

    def add_snippet(self):
        trigger = self.trigger_input.text().strip().lower()
        expansion = self.expansion_input.text().strip()
        if trigger and expansion:
            snippets = self.config_manager.get("snippets", {})
            snippets[trigger] = expansion
            self.config_manager.set("snippets", snippets)
            self.load_snippets()
            self.trigger_input.clear()
            self.expansion_input.clear()

    def remove_snippet(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            trigger = self.table_widget.item(selected_row, 0).text()
            snippets = self.config_manager.get("snippets", {})
            if trigger in snippets:
                del snippets[trigger]
                self.config_manager.set("snippets", snippets)
                self.load_snippets()
