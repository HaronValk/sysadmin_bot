import sqlite3
from config import DB_PATH


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS lessons_cache (
                lesson_id INTEGER PRIMARY KEY,
                content TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER PRIMARY KEY,
                last_lesson_id INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, lesson_id)
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                project_track TEXT DEFAULT 'ru'
            );
            CREATE TABLE IF NOT EXISTS project_progress (
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                completed INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, lesson_id)
            );
        """)


def _fetch_one(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(query, params).fetchone()


def _fetch_all(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(query, params).fetchall()


def _execute(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(query, params)
        conn.commit()


def get_cached_lesson(lid):
    row = _fetch_one("SELECT content FROM lessons_cache WHERE lesson_id=?", (lid,))
    return row[0] if row else None


def load_progress(uid):
    row = _fetch_one("SELECT last_lesson_id FROM progress WHERE user_id=?", (uid,))
    return row[0] if row else 0


def save_progress(uid, lid):
    _execute("INSERT OR REPLACE INTO progress VALUES (?,?)", (uid, lid))


def reset_progress(uid):
    _execute("DELETE FROM progress WHERE user_id=?", (uid,))


def add_favorite(uid, lid):
    _execute("INSERT OR IGNORE INTO favorites VALUES (?,?)", (uid, lid))


def remove_favorite(uid, lid):
    _execute("DELETE FROM favorites WHERE user_id=? AND lesson_id=?", (uid, lid))


def get_favorite_ids(uid):
    return [
        r[0]
        for r in _fetch_all(
            "SELECT lesson_id FROM favorites WHERE user_id=? ORDER BY lesson_id", (uid,)
        )
    ]


def is_favorite(uid, lid):
    return lid in get_favorite_ids(uid)


def add_note(uid, text):
    _execute("INSERT INTO notes (user_id, content) VALUES (?,?)", (uid, text))


def get_notes(uid):
    return _fetch_all(
        "SELECT id, content, created_at FROM notes WHERE user_id=? ORDER BY created_at DESC",
        (uid,),
    )


def delete_note(uid, nid):
    _execute("DELETE FROM notes WHERE user_id=? AND id=?", (uid, nid))


def record_token_usage(uid, tokens, cost):
    _execute(
        "INSERT INTO token_usage (user_id, tokens, cost) VALUES (?,?,?)",
        (uid, tokens, cost),
    )


def get_token_summary(uid):
    row = _fetch_one(
        "SELECT COALESCE(SUM(tokens),0), COALESCE(SUM(cost),0) FROM token_usage WHERE user_id=?",
        (uid,),
    )
    return (row[0] or 0, row[1] or 0.0)


def set_project_track(uid, track):
    _execute("INSERT OR REPLACE INTO user_settings VALUES (?, ?)", (uid, track))


def get_project_track(uid):
    row = _fetch_one("SELECT project_track FROM user_settings WHERE user_id=?", (uid,))
    return row[0] if row else "ru"


def complete_project_step(uid, lid):
    _execute("INSERT OR REPLACE INTO project_progress VALUES (?, ?, 1)", (uid, lid))


def get_completed_project_steps(uid):
    return [
        r[0]
        for r in _fetch_all(
            "SELECT lesson_id FROM project_progress WHERE user_id=? ORDER BY lesson_id",
            (uid,),
        )
    ]
