"""Tests for database.py. Run from the project folder: python -m unittest discover -s tests -v"""

import json
import os
import tempfile
import unittest
from datetime import date, timedelta

import database as db


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        os.environ["HERSPACE_DB_PATH"] = os.path.join(self.folder.name, "test.db")
        db.init_db()

    def tearDown(self):
        os.environ.pop("HERSPACE_DB_PATH", None)
        self.folder.cleanup()


class TestSetup(DatabaseTestCase):
    def test_tables_created_and_empty(self):
        self.assertFalse(db.has_any_data())
        self.assertEqual(db.get_journal_entries(), [])
        self.assertEqual(db.get_recent_activity(), [])

    def test_init_twice_is_safe(self):
        db.init_db()
        db.init_db()


class TestJournal(DatabaseTestCase):
    def test_create_edit_delete(self):
        entry_id = db.add_journal_entry("Day one", "Hello diary", date(2026, 10, 1), "Happy")
        entry = db.get_journal_entry(entry_id)
        self.assertEqual(entry["title"], "Day one")
        self.assertEqual(entry["mood"], "Happy")
        db.update_journal_entry(entry_id, "Renamed", "New text", date(2026, 10, 2), "")
        entry = db.get_journal_entry(entry_id)
        self.assertEqual((entry["title"], entry["content"], entry["entry_date"]),
                         ("Renamed", "New text", "2026-10-02"))
        db.delete_journal_entry(entry_id)
        self.assertIsNone(db.get_journal_entry(entry_id))

    def test_empty_content_rejected(self):
        with self.assertRaises(ValueError):
            db.add_journal_entry("Title", "   ", date.today())

    def test_invalid_mood_rejected(self):
        with self.assertRaises(ValueError):
            db.add_journal_entry("T", "text", date.today(), "Confused")

    def test_search_and_special_characters(self):
        db.add_journal_entry("Garden", "I planted roses", date.today())
        db.add_journal_entry("Work", "Finished 100% of the report", date.today())
        self.assertEqual(len(db.get_journal_entries("roses")), 1)
        self.assertEqual(len(db.get_journal_entries("garden")), 1)
        self.assertEqual(len(db.get_journal_entries("100%")), 1)
        self.assertEqual(len(db.get_journal_entries("'; DROP TABLE journal_entries; --")), 0)
        self.assertEqual(len(db.get_journal_entries()), 2)  # table still exists


class TestMood(DatabaseTestCase):
    def test_add_filter_update_delete(self):
        today = date.today()
        old = today - timedelta(days=20)
        mood_id = db.add_mood(today, "Calm", "quiet day")
        db.add_mood(old, "Stressed")
        self.assertEqual(len(db.get_moods()), 2)
        self.assertEqual(len(db.get_moods(today - timedelta(days=7), today)), 1)
        db.update_mood(mood_id, today, "Grateful", "")
        self.assertEqual(db.get_moods(today, today)[0]["mood"], "Grateful")
        db.delete_mood(mood_id)
        self.assertEqual(len(db.get_moods()), 1)

    def test_invalid_mood(self):
        with self.assertRaises(ValueError):
            db.add_mood(date.today(), "Bored")


class TestSelfCare(DatabaseTestCase):
    def test_routine_lifecycle_and_completion(self):
        rid = db.add_routine("Face mask", "Sunday treat", "Skincare", "Weekly", "Sunday")
        sunday = date(2026, 10, 25)  # a Sunday
        monday = date(2026, 10, 26)
        self.assertEqual(len(db.get_routines_due(sunday)), 1)
        self.assertEqual(len(db.get_routines_due(monday)), 0)

        db.set_routine_done(rid, sunday, True)
        db.set_routine_done(rid, sunday, True)  # twice must not duplicate
        self.assertEqual(db.get_done_routine_ids(sunday), {rid})
        db.set_routine_done(rid, sunday, False)
        self.assertEqual(db.get_done_routine_ids(sunday), set())

        db.update_routine(rid, "Hair mask", "", "Haircare", "Daily")
        self.assertEqual(db.get_routines()[0]["name"], "Hair mask")
        db.delete_routine(rid)
        self.assertEqual(db.get_routines(), [])

    def test_frequencies(self):
        db.add_routine("Daily one", "", "Other", "Daily")
        db.add_routine("Weekday one", "", "Other", "Weekdays")
        db.add_routine("Weekend one", "", "Other", "Weekends")
        monday, saturday = date(2026, 10, 26), date(2026, 10, 24)
        self.assertEqual({r["name"] for r in db.get_routines_due(monday)}, {"Daily one", "Weekday one"})
        self.assertEqual({r["name"] for r in db.get_routines_due(saturday)}, {"Daily one", "Weekend one"})

    def test_validation(self):
        with self.assertRaises(ValueError):
            db.add_routine("", "", "Skincare", "Daily")
        with self.assertRaises(ValueError):
            db.add_routine("x", "", "Nonsense", "Daily")
        with self.assertRaises(ValueError):
            db.add_routine("x", "", "Skincare", "Weekly", "")  # weekly needs a day

    def test_deleting_routine_removes_history(self):
        rid = db.add_routine("Bath", "", "Relaxation", "Daily")
        db.set_routine_done(rid, date.today(), True)
        self.assertEqual(len(db.get_routine_history()), 1)
        db.delete_routine(rid)
        self.assertEqual(db.get_routine_history(), [])


class TestGoals(DatabaseTestCase):
    def test_goal_progress_edit_delete(self):
        gid = db.add_goal("Learn SQL", "Study basics", 10, "30 min/day", date(2026, 12, 1), "evenings")
        goal = db.get_goal(gid)
        self.assertEqual((goal["progress"], goal["target_date"]), (10, "2026-12-01"))
        db.update_goal_progress(gid, 55)
        self.assertEqual(db.get_goal(gid)["progress"], 55)
        db.update_goal(gid, "Learn SQL well", "", 60, "", None, "")
        self.assertIsNone(db.get_goal(gid)["target_date"])
        self.assertEqual(len(db.get_goals(active_only=True)), 1)
        db.update_goal_progress(gid, 100)
        self.assertEqual(db.get_goals(active_only=True), [])
        db.delete_goal(gid)
        self.assertEqual(db.get_goals(), [])

    def test_invalid_progress_and_title(self):
        with self.assertRaises(ValueError):
            db.add_goal("", "", 0)
        with self.assertRaises(ValueError):
            db.add_goal("Goal", "", 150)
        with self.assertRaises(ValueError):
            db.add_goal("Goal", "", "abc")

    def test_plan_and_milestones(self):
        gid = db.add_goal("Read more")
        plan = {"summary": "s", "steps": ["a"], "timeline": "t", "weekly_milestones": ["Week 1: x"],
                "checklist": ["Pick a book", "Read 10 pages", "  "], "encouragement": "go"}
        db.save_goal_plan(gid, plan)
        self.assertEqual(json.loads(db.get_goal(gid)["plan_json"])["summary"], "s")
        milestones = db.get_milestones(gid)
        self.assertEqual([m["title"] for m in milestones], ["Pick a book", "Read 10 pages"])
        db.set_milestone_done(milestones[0]["id"], True)
        self.assertEqual(db.get_milestones(gid)[0]["is_done"], 1)
        db.save_goal_plan(gid, plan)  # regenerate replaces old checklist
        self.assertEqual(len(db.get_milestones(gid)), 2)
        db.delete_goal(gid)
        self.assertEqual(db.get_milestones(gid), [])


class TestHabits(DatabaseTestCase):
    def test_habit_lifecycle(self):
        hid = db.add_habit("Practice Python", "daily coding", "Daily")
        today = date.today()
        db.set_habit_done(hid, today, True)
        db.set_habit_done(hid, today, True)
        self.assertEqual(db.get_done_habit_ids(today), {hid})
        db.set_habit_done(hid, today, False)
        self.assertEqual(db.get_done_habit_ids(today), set())
        db.update_habit(hid, "Practice SQL", "", "Weekdays")
        self.assertEqual(db.get_habits()[0]["frequency"], "Weekdays")
        db.delete_habit(hid)
        self.assertEqual(db.get_habits(), [])

    def test_streak_and_stats_use_real_records(self):
        hid = db.add_habit("Read", "", "Daily")
        today = date.today()
        self.assertEqual(db.get_habit_stats(hid)["streak"], 0)  # nothing invented
        for offset in (0, 1, 2, 4):  # a gap on day 3
            db.set_habit_done(hid, today - timedelta(days=offset), True)
        stats = db.get_habit_stats(hid, today)
        self.assertEqual(stats["streak"], 3)
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["last_7_days"], 4)

    def test_streak_alive_if_done_yesterday(self):
        today = date(2026, 10, 23)
        dates = {today - timedelta(days=1), today - timedelta(days=2)}
        self.assertEqual(db.calculate_streak(dates, today), 2)
        self.assertEqual(db.calculate_streak({today - timedelta(days=3)}, today), 0)
        self.assertEqual(db.calculate_streak(set(), today), 0)

    def test_daily_counts_and_history(self):
        h1, h2 = db.add_habit("A", "", "Daily"), db.add_habit("B", "", "Daily")
        today = date.today()
        db.set_habit_done(h1, today, True)
        db.set_habit_done(h2, today, True)
        counts = db.get_habit_daily_counts(14)
        self.assertEqual(len(counts), 14)
        self.assertEqual(counts[-1]["completed"], 2)
        self.assertEqual(sum(c["completed"] for c in counts[:-1]), 0)
        self.assertEqual(len(db.get_habit_history()), 2)


class TestFavorites(DatabaseTestCase):
    def test_add_duplicate_remove(self):
        self.assertTrue(db.add_favorite("I am enough."))
        self.assertFalse(db.add_favorite("I am enough."))
        self.assertTrue(db.is_favorite("I am enough."))
        favorites = db.get_favorites()
        self.assertEqual(len(favorites), 1)
        db.remove_favorite(favorites[0]["id"])
        self.assertFalse(db.is_favorite("I am enough."))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            db.add_favorite("  ")


class TestExportAndDelete(DatabaseTestCase):
    def test_recent_activity_export_and_delete_all(self):
        db.add_journal_entry("t", "private text", date.today())
        db.add_mood(date.today(), "Happy")
        hid = db.add_habit("Walk", "", "Daily")
        db.set_habit_done(hid, date.today(), True)
        db.add_goal("Goal")
        activity = " ".join(a["text"] for a in db.get_recent_activity(10))
        self.assertIn("journal entry", activity)
        self.assertNotIn("private text", activity)  # activity feed never shows entry text
        self.assertIn("Walk", activity)

        data = db.export_all_data()
        self.assertEqual(set(data["tables"]), set(db.TABLES))
        self.assertEqual(len(data["tables"]["journal_entries"]), 1)
        json.dumps(data)  # must be JSON-serializable

        self.assertTrue(db.has_any_data())
        db.delete_all_data()
        self.assertFalse(db.has_any_data())
        for rows in db.export_all_data()["tables"].values():
            self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
