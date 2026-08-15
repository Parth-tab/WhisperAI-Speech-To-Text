from src.data.stats_store import StatsStore


def test_stats_store_empty_defaults(tmp_path):
    db_file = tmp_path / "test_stats.db"
    store = StatsStore(db_path=str(db_file))

    totals = store.get_totals()
    assert totals["total_sessions"] == 0
    assert totals["total_words"] == 0
    assert totals["total_chars"] == 0
    assert totals["total_duration_sec"] == 0.0
    assert totals["avg_wpm"] == 0


def test_stats_store_log_and_totals(tmp_path):
    db_file = tmp_path / "test_stats.db"
    store = StatsStore(db_path=str(db_file))

    # 10 words, 50 chars in 5 seconds -> (10 / 5) * 60 = 120 WPM
    store.log_session(duration_sec=5.0, text="one two three four five six seven eight nine ten")

    totals = store.get_totals()
    assert totals["total_sessions"] == 1
    assert totals["total_words"] == 10
    assert totals["total_duration_sec"] == 5.0
    assert totals["avg_wpm"] == 120.0

    # Add second session: 20 words in 10 seconds -> total 30 words in 15 seconds -> 120 WPM
    store.log_session(duration_sec=10.0, text=" ".join(["word"] * 20))

    totals2 = store.get_totals()
    assert totals2["total_sessions"] == 2
    assert totals2["total_words"] == 30
    assert totals2["total_duration_sec"] == 15.0
    assert totals2["avg_wpm"] == 120.0


def test_stats_store_empty_text_ignored(tmp_path):
    db_file = tmp_path / "test_stats.db"
    store = StatsStore(db_path=str(db_file))

    store.log_session(duration_sec=5.0, text="")
    totals = store.get_totals()
    assert totals["total_sessions"] == 0
