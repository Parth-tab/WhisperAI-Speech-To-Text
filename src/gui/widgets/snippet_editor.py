from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


class SnippetEditor(QWidget):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget(0, 2)
        self.table_widget.setHorizontalHeaderLabels(
            ["Trigger Phrase", "Expansion Text (Multi-Line / Templates)"]
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_snippets()
        layout.addWidget(self.table_widget)

        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("Trigger phrase (e.g. 'insert template', 'standup update')...")
        layout.addWidget(self.trigger_input)

        self.expansion_input = QPlainTextEdit()
        self.expansion_input.setMaximumHeight(90)
        self.expansion_input.setPlaceholderText(
            "Expansion template... (Supports {date}, {time}, {clipboard})"
        )
        layout.addWidget(self.expansion_input)

        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("Add / Update Snippet")
        self.add_button.clicked.connect(self.add_snippet)
        btn_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_snippet)
        btn_layout.addWidget(self.remove_button)
        layout.addLayout(btn_layout)

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
        expansion = self.expansion_input.toPlainText().strip()
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
