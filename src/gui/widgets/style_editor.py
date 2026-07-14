from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
)

from src.llm.style_profiles import STYLE_PROFILES


class StyleEditor(QWidget):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget(0, 2)
        self.table_widget.setHorizontalHeaderLabels(
            ["Process Name (e.g. slack.exe)", "Style Profile"]
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.load_styles()
        layout.addWidget(self.table_widget)

        input_layout = QHBoxLayout()
        self.process_input = QLineEdit()
        self.process_input.setPlaceholderText("Process (e.g. slack.exe)")
        input_layout.addWidget(self.process_input)

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list(STYLE_PROFILES.keys()))
        input_layout.addWidget(self.profile_combo)

        self.add_button = QPushButton("Map Style")
        self.add_button.clicked.connect(self.add_style_mapping)
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_style_mapping)
        layout.addWidget(self.remove_button)

    def load_styles(self):
        self.table_widget.setRowCount(0)
        app_styles = self.config_manager.get("app_styles", {})
        for process, profile in app_styles.items():
            row_pos = self.table_widget.rowCount()
            self.table_widget.insertRow(row_pos)
            self.table_widget.setItem(row_pos, 0, QTableWidgetItem(process))
            self.table_widget.setItem(row_pos, 1, QTableWidgetItem(profile))

    def add_style_mapping(self):
        process = self.process_input.text().strip().lower()
        profile = self.profile_combo.currentText()
        if process and profile:
            app_styles = self.config_manager.get("app_styles", {})
            app_styles[process] = profile
            self.config_manager.set("app_styles", app_styles)
            self.load_styles()
            self.process_input.clear()

    def remove_style_mapping(self):
        selected_row = self.table_widget.currentRow()
        if selected_row >= 0:
            process = self.table_widget.item(selected_row, 0).text()
            app_styles = self.config_manager.get("app_styles", {})
            if process in app_styles:
                del app_styles[process]
                self.config_manager.set("app_styles", app_styles)
                self.load_styles()
