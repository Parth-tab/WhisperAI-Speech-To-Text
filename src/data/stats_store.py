import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import closing


class StatsStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = Path.home() / ".whisperai" / "stats.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_time TEXT,
                        end_time TEXT,
                        word_count INTEGER,
                        char_count INTEGER,
                        duration_sec REAL
                    )
                """)

    def log_session(self, duration_sec: float, text: str):
        if not text:
            return

        word_count = len(text.split())
        char_count = len(text)

        now = datetime.now()
        start_time_str = (now - timedelta(seconds=duration_sec)).isoformat()
        end_time_str = now.isoformat()

        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO sessions (start_time, end_time, word_count, char_count, duration_sec)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        start_time_str,
                        end_time_str,
                        word_count,
                        char_count,
                        duration_sec,
                    ),
                )

    def get_totals(self) -> dict:
        with closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(id),
                        SUM(word_count),
                        SUM(char_count),
                        SUM(duration_sec)
                    FROM sessions
                """)
                row = cursor.fetchone()

        total_sessions = row[0] or 0
        total_words = row[1] or 0
        total_chars = row[2] or 0
        total_duration = row[3] or 0.0

        avg_wpm = 0
        if total_duration > 0:
            avg_wpm = (total_words / total_duration) * 60.0

        return {
            "total_sessions": total_sessions,
            "total_words": total_words,
            "total_chars": total_chars,
            "total_duration_sec": total_duration,
            "avg_wpm": avg_wpm,
        }


stats_store = StatsStore()
