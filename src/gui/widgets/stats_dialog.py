from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFormLayout
from PySide6.QtCore import Qt
from src.data.stats_store import stats_store


class StatsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Usage Insights")
        self.setFixedSize(300, 250)

        layout = QVBoxLayout(self)

        title = QLabel("<b>Your Usage Stats</b>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form_layout = QFormLayout()

        stats = stats_store.get_totals()

        form_layout.addRow("Total Dictations:", QLabel(str(stats["total_sessions"])))
        form_layout.addRow("Words Dictated:", QLabel(f"{stats['total_words']:,}"))
        form_layout.addRow("Characters Typed:", QLabel(f"{stats['total_chars']:,}"))

        duration_mins = stats["total_duration_sec"] / 60.0
        form_layout.addRow("Time Dictating:", QLabel(f"{duration_mins:.1f} mins"))

        wpm_label = QLabel(f"{stats['avg_wpm']:.1f} WPM")
        wpm_label.setStyleSheet("color: #4ade80; font-weight: bold;")
        form_layout.addRow("Average Speed:", wpm_label)

        layout.addLayout(form_layout)
        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
