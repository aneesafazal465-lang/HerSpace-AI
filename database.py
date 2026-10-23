"""
database.py - all SQLite storage for HerSpace AI.

Every function here talks to the database using parameterized SQL
(the "?" placeholders), so user text can never break the queries.
Dates are saved as text in ISO format, for example "2026-10-23".
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

# --------------------------------------------------------------------------
# Constants used by the app and by validation
# --------------------------------------------------------------------------

DEFAULT_DB_PATH = Path(__file__).parent / "data" / "herspace.db"

MOOD_OPTIONS = {
    "Happy": "😊",
    "Calm": "🌿",
    "Excited": "✨",
    "Grateful": "💗",
    "Tired": "😴",
    "Stressed": "🌧️",
    "Sad": "💙",
    "Overwhelmed": "🫧",
}

SELFCARE_CATEGORIES = [
    "Skincare", "Haircare", "Relaxation", "Reading",
    "Personal care", "Hobbies", "Other",
]
SELFCARE_FREQUENCIES = ["Daily", "Weekdays", "Weekends", "Weekly", "As needed"]
HABIT_FREQUENCIES = ["Daily", "Weekdays", "Weekly"]
WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

TABLES = [
    "journal_entries", "mood_records", "selfcare_routines",
    "selfcare_completions", "goals", "goal_milestones",
    "habits", "habit_completions", "favorite_affirmations",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    entry_date TEXT NOT NULL,
    mood TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mood_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mood TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    mood_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS selfcare_routines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL,
    frequency TEXT NOT NULL,
    schedule_day TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS selfcare_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    routine_id INTEGER NOT NULL REFERENCES selfcare_routines(id) ON DELETE CASCADE,
    completed_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (routine_id, completed_date)
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    progress INTEGER NOT NULL DEFAULT 0,
    available_time TEXT NOT NULL DEFAULT '',
    target_date TEXT,
    preferences TEXT NOT NULL DEFAULT '',
    plan_json TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS goal_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    is_done INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    frequency TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS habit_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    completed_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (habit_id, completed_date)
);
CREATE TABLE IF NOT EXISTS favorite_affirmations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
"""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def get_db_path():
    """Where the database file lives (can be changed with HERSPACE_DB_PATH)."""
    return Path(os.environ.get("HERSPACE_DB_PATH", str(DEFAULT_DB_PATH)))


@contextmanager
def get_connection():
    """Open a connection, save changes at the end, and always close it."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not exist yet."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def _query(sql, params=()):
    """Run a SELECT and return a list of plain dictionaries."""
    with get_connection() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def _execute(sql, params=()):
    """Run INSERT / UPDATE / DELETE. Returns the new row id (for inserts)."""
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _to_iso(value):
    """Accept a date, datetime or 'YYYY-MM-DD' text and return ISO text."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValueError("Please choose a valid date.")


def _required_text(value, label, max_len=10000):
    """Trim text and make sure it is not empty."""
    text = (value or "").strip()
    if not text:
        raise ValueError(f"Please fill in the {label}.")
    return text[:max_len]


def _optional_text(value, max_len=10000):
    return (value or "").strip()[:max_len]


def _choice(value, allowed, label):
    if value not in allowed:
        raise ValueError(f"Please choose a valid {label}.")
    return value


# --------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------

def add_journal_entry(title, content, entry_date, mood=""):
    content = _required_text(content, "journal entry")
    if mood:
        _choice(mood, MOOD_OPTIONS, "mood")
    now = _now()
    return _execute(
        "INSERT INTO journal_entries (title, content, entry_date, mood, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (_optional_text(title, 200), content, _to_iso(entry_date) or date.today().isoformat(),
         mood or "", now, now),
    )


def update_journal_entry(entry_id, title, content, entry_date, mood=""):
    content = _required_text(content, "journal entry")
    if mood:
        _choice(mood, MOOD_OPTIONS, "mood")
    _execute(
        "UPDATE journal_entries SET title = ?, content = ?, entry_date = ?, mood = ?, updated_at = ? "
        "WHERE id = ?",
        (_optional_text(title, 200), content, _to_iso(entry_date) or date.today().isoformat(),
         mood or "", _now(), entry_id),
    )


def delete_journal_entry(entry_id):
    _execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))


def get_journal_entry(entry_id):
    rows = _query("SELECT * FROM journal_entries WHERE id = ?", (entry_id,))
    return rows[0] if rows else None


def get_journal_entries(search=None):
    """All entries, newest first. `search` looks in the title and the text."""
    search = (search or "").strip()
    if not search:
        return _query("SELECT * FROM journal_entries ORDER BY entry_date DESC, id DESC")
    escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return _query(
        "SELECT * FROM journal_entries "
        "WHERE title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\' "
        "ORDER BY entry_date DESC, id DESC",
        (pattern, pattern),
    )


# --------------------------------------------------------------------------
# Mood tracker
# --------------------------------------------------------------------------

def add_mood(mood_date, mood, note=""):
    _choice(mood, MOOD_OPTIONS, "mood")
    return _execute(
        "INSERT INTO mood_records (mood, note, mood_date, created_at) VALUES (?, ?, ?, ?)",
        (mood, _optional_text(note, 1000), _to_iso(mood_date) or date.today().isoformat(), _now()),
    )


def update_mood(mood_id, mood_date, mood, note=""):
    _choice(mood, MOOD_OPTIONS, "mood")
    _execute(
        "UPDATE mood_records SET mood = ?, note = ?, mood_date = ? WHERE id = ?",
        (mood, _optional_text(note, 1000), _to_iso(mood_date), mood_id),
    )


def delete_mood(mood_id):
    _execute("DELETE FROM mood_records WHERE id = ?", (mood_id,))


def get_moods(start=None, end=None):
    """Mood records (newest first), optionally between two dates (inclusive)."""
    sql = "SELECT * FROM mood_records WHERE 1 = 1"
    params = []
    if start:
        sql += " AND mood_date >= ?"
        params.append(_to_iso(start))
    if end:
        sql += " AND mood_date <= ?"
        params.append(_to_iso(end))
    sql += " ORDER BY mood_date DESC, id DESC"
    return _query(sql, tuple(params))


# --------------------------------------------------------------------------
# Self-care routines
# --------------------------------------------------------------------------

def _check_schedule(frequency, schedule_day):
    _choice(frequency, SELFCARE_FREQUENCIES, "frequency")
    if frequency == "Weekly":
        _choice(schedule_day, WEEKDAY_NAMES, "day of the week")
        return schedule_day
    return ""


def add_routine(name, description, category, frequency, schedule_day=""):
    name = _required_text(name, "routine name", 150)
    _choice(category, SELFCARE_CATEGORIES, "category")
    schedule_day = _check_schedule(frequency, schedule_day)
    return _execute(
        "INSERT INTO selfcare_routines (name, description, category, frequency, schedule_day, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, _optional_text(description, 1000), category, frequency, schedule_day, _now()),
    )


def update_routine(routine_id, name, description, category, frequency, schedule_day=""):
    name = _required_text(name, "routine name", 150)
    _choice(category, SELFCARE_CATEGORIES, "category")
    schedule_day = _check_schedule(frequency, schedule_day)
    _execute(
        "UPDATE selfcare_routines SET name = ?, description = ?, category = ?, frequency = ?, "
        "schedule_day = ? WHERE id = ?",
        (name, _optional_text(description, 1000), category, frequency, schedule_day, routine_id),
    )


def delete_routine(routine_id):
    _execute("DELETE FROM selfcare_routines WHERE id = ?", (routine_id,))


def get_routines():
    return _query("SELECT * FROM selfcare_routines ORDER BY category, name")


def is_due_on(routine, day):
    """Is this routine planned for the given day?"""
    frequency = routine["frequency"]
    if frequency == "Weekdays":
        return day.weekday() < 5
    if frequency == "Weekends":
        return day.weekday() >= 5
    if frequency == "Weekly":
        return routine["schedule_day"] == WEEKDAY_NAMES[day.weekday()]
    return True  # Daily and "As needed" always appear


def get_routines_due(day):
    return [r for r in get_routines() if is_due_on(r, day)]


def set_routine_done(routine_id, day, done):
    day_iso = _to_iso(day)
    if done:
        _execute(
            "INSERT OR IGNORE INTO selfcare_completions (routine_id, completed_date, created_at) "
            "VALUES (?, ?, ?)",
            (routine_id, day_iso, _now()),
        )
    else:
        _execute(
            "DELETE FROM selfcare_completions WHERE routine_id = ? AND completed_date = ?",
            (routine_id, day_iso),
        )


def get_done_routine_ids(day):
    rows = _query("SELECT routine_id FROM selfcare_completions WHERE completed_date = ?", (_to_iso(day),))
    return {row["routine_id"] for row in rows}


def get_routine_history(days=30):
    since = (date.today() - timedelta(days=days)).isoformat()
    return _query(
        "SELECT c.completed_date, r.name, r.category FROM selfcare_completions c "
        "JOIN selfcare_routines r ON r.id = c.routine_id "
        "WHERE c.completed_date >= ? ORDER BY c.completed_date DESC, r.name",
        (since,),
    )


# --------------------------------------------------------------------------
# Goals and milestones
# --------------------------------------------------------------------------

def _check_progress(progress):
    try:
        progress = int(progress)
    except (TypeError, ValueError):
        raise ValueError("Progress must be a number between 0 and 100.")
    if not 0 <= progress <= 100:
        raise ValueError("Progress must be between 0 and 100.")
    return progress


def add_goal(title, description="", progress=0, available_time="", target_date=None, preferences=""):
    title = _required_text(title, "goal title", 200)
    now = _now()
    return _execute(
        "INSERT INTO goals (title, description, progress, available_time, target_date, preferences, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (title, _optional_text(description, 3000), _check_progress(progress),
         _optional_text(available_time, 200), _to_iso(target_date),
         _optional_text(preferences, 2000), now, now),
    )


def update_goal(goal_id, title, description, progress, available_time, target_date, preferences):
    title = _required_text(title, "goal title", 200)
    _execute(
        "UPDATE goals SET title = ?, description = ?, progress = ?, available_time = ?, "
        "target_date = ?, preferences = ?, updated_at = ? WHERE id = ?",
        (title, _optional_text(description, 3000), _check_progress(progress),
         _optional_text(available_time, 200), _to_iso(target_date),
         _optional_text(preferences, 2000), _now(), goal_id),
    )


def update_goal_progress(goal_id, progress):
    _execute("UPDATE goals SET progress = ?, updated_at = ? WHERE id = ?",
             (_check_progress(progress), _now(), goal_id))


def delete_goal(goal_id):
    _execute("DELETE FROM goals WHERE id = ?", (goal_id,))


def get_goal(goal_id):
    rows = _query("SELECT * FROM goals WHERE id = ?", (goal_id,))
    return rows[0] if rows else None


def get_goals(active_only=False):
    sql = "SELECT * FROM goals"
    if active_only:
        sql += " WHERE progress < 100"
    return _query(sql + " ORDER BY progress >= 100, created_at DESC")


def save_goal_plan(goal_id, plan):
    """Save an AI plan (a dictionary) and turn its checklist into milestones."""
    import json
    checklist = [str(item).strip() for item in plan.get("checklist", []) if str(item).strip()]
    with get_connection() as conn:
        conn.execute("UPDATE goals SET plan_json = ?, updated_at = ? WHERE id = ?",
                     (json.dumps(plan, ensure_ascii=False), _now(), goal_id))
        conn.execute("DELETE FROM goal_milestones WHERE goal_id = ?", (goal_id,))
        for position, item in enumerate(checklist):
            conn.execute(
                "INSERT INTO goal_milestones (goal_id, title, is_done, position) VALUES (?, ?, 0, ?)",
                (goal_id, item[:300], position),
            )


def get_milestones(goal_id):
    return _query("SELECT * FROM goal_milestones WHERE goal_id = ? ORDER BY position, id", (goal_id,))


def set_milestone_done(milestone_id, done):
    _execute("UPDATE goal_milestones SET is_done = ? WHERE id = ?", (1 if done else 0, milestone_id))


# --------------------------------------------------------------------------
# Habits
# --------------------------------------------------------------------------

def add_habit(name, description, frequency):
    name = _required_text(name, "habit name", 150)
    _choice(frequency, HABIT_FREQUENCIES, "frequency")
    return _execute(
        "INSERT INTO habits (name, description, frequency, created_at) VALUES (?, ?, ?, ?)",
        (name, _optional_text(description, 1000), frequency, _now()),
    )


def update_habit(habit_id, name, description, frequency):
    name = _required_text(name, "habit name", 150)
    _choice(frequency, HABIT_FREQUENCIES, "frequency")
    _execute("UPDATE habits SET name = ?, description = ?, frequency = ? WHERE id = ?",
             (name, _optional_text(description, 1000), frequency, habit_id))


def delete_habit(habit_id):
    _execute("DELETE FROM habits WHERE id = ?", (habit_id,))


def get_habits():
    return _query("SELECT * FROM habits ORDER BY name")


def habit_is_due_on(habit, day):
    if habit["frequency"] == "Weekdays":
        return day.weekday() < 5
    return True  # Daily and Weekly habits can be ticked on any day


def set_habit_done(habit_id, day, done):
    day_iso = _to_iso(day)
    if done:
        _execute(
            "INSERT OR IGNORE INTO habit_completions (habit_id, completed_date, created_at) VALUES (?, ?, ?)",
            (habit_id, day_iso, _now()),
        )
    else:
        _execute("DELETE FROM habit_completions WHERE habit_id = ? AND completed_date = ?",
                 (habit_id, day_iso))


def get_done_habit_ids(day):
    rows = _query("SELECT habit_id FROM habit_completions WHERE completed_date = ?", (_to_iso(day),))
    return {row["habit_id"] for row in rows}


def calculate_streak(done_dates, today):
    """
    Count how many days in a row the habit was checked off.
    A streak is still alive if the last check-in was today or yesterday.
    `done_dates` is a set of date objects.
    """
    current = today if today in done_dates else today - timedelta(days=1)
    streak = 0
    while current in done_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def get_habit_stats(habit_id, today=None):
    """Real numbers calculated from the saved completion records."""
    today = today or date.today()
    rows = _query("SELECT completed_date FROM habit_completions WHERE habit_id = ?", (habit_id,))
    done_dates = {date.fromisoformat(r["completed_date"]) for r in rows}
    return {
        "total": len(done_dates),
        "last_7_days": sum(1 for d in done_dates if 0 <= (today - d).days < 7),
        "last_30_days": sum(1 for d in done_dates if 0 <= (today - d).days < 30),
        "streak": calculate_streak(done_dates, today),
    }


def get_habit_daily_counts(days=14):
    """How many habits were completed on each of the last `days` days."""
    today = date.today()
    since = (today - timedelta(days=days - 1)).isoformat()
    rows = _query(
        "SELECT completed_date, COUNT(*) AS count FROM habit_completions "
        "WHERE completed_date >= ? GROUP BY completed_date",
        (since,),
    )
    counts = {r["completed_date"]: r["count"] for r in rows}
    result = []
    for offset in range(days - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        result.append({"date": day, "completed": counts.get(day, 0)})
    return result


def get_habit_history(days=30):
    since = (date.today() - timedelta(days=days)).isoformat()
    return _query(
        "SELECT c.completed_date, h.name FROM habit_completions c "
        "JOIN habits h ON h.id = c.habit_id WHERE c.completed_date >= ? "
        "ORDER BY c.completed_date DESC, h.name",
        (since,),
    )


# --------------------------------------------------------------------------
# Favorite affirmations
# --------------------------------------------------------------------------

def add_favorite(text):
    """Returns True if saved, False if it was already a favorite."""
    text = _required_text(text, "affirmation", 500)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO favorite_affirmations (text, created_at) VALUES (?, ?)",
            (text, _now()),
        )
        return cursor.rowcount > 0


def get_favorites():
    return _query("SELECT * FROM favorite_affirmations ORDER BY id DESC")


def is_favorite(text):
    return bool(_query("SELECT 1 FROM favorite_affirmations WHERE text = ?", ((text or "").strip(),)))


def remove_favorite(favorite_id):
    _execute("DELETE FROM favorite_affirmations WHERE id = ?", (favorite_id,))


# --------------------------------------------------------------------------
# Home page helpers, export and delete
# --------------------------------------------------------------------------

def get_recent_activity(limit=6):
    """A mixed list of the latest things the user actually did."""
    return _query(
        "SELECT ts, text FROM ("
        " SELECT created_at AS ts, '📔 Wrote a journal entry' AS text FROM journal_entries"
        " UNION ALL SELECT created_at, '🌸 Logged a mood: ' || mood FROM mood_records"
        " UNION ALL SELECT c.created_at, '✨ Completed habit: ' || h.name FROM habit_completions c"
        "   JOIN habits h ON h.id = c.habit_id"
        " UNION ALL SELECT c.created_at, '🧴 Finished routine: ' || r.name FROM selfcare_completions c"
        "   JOIN selfcare_routines r ON r.id = c.routine_id"
        " UNION ALL SELECT created_at, '🎯 Started a goal: ' || title FROM goals"
        ") ORDER BY ts DESC LIMIT ?",
        (int(limit),),
    )


def export_all_data():
    """Everything saved in the app, as a dictionary ready to become JSON."""
    return {
        "exported_at": _now(),
        "app": "HerSpace AI",
        "tables": {table: _query(f"SELECT * FROM {table}") for table in TABLES},
    }


def delete_all_data():
    """Remove every saved row (the empty tables stay)."""
    with get_connection() as conn:
        for table in TABLES:
            conn.execute(f"DELETE FROM {table}")


def has_any_data():
    with get_connection() as conn:
        for table in ("journal_entries", "mood_records", "selfcare_routines",
                      "goals", "habits", "favorite_affirmations"):
            if conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():
                return True
    return False
