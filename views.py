"""
views.py - one function per page of HerSpace AI.

Each *_page() function draws a page. Shared helpers are at the top.
Anything the user typed is passed through esc() before it goes inside
HTML cards, so it can never break the page.
"""

import html
import json
import random
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import ai_service as ai
import database as db
from styles import PALETTE

TAGLINE = "Your little corner to grow, glow, and become your best self."
APP_VERSION = "1.0.0"

# Home links to the other pages. app.py fills this in.
PAGES = {}

MOOD_LABELS = {f"{emoji} {name}": name for name, emoji in db.MOOD_OPTIONS.items()}
MOOD_COLORS = {
    "Happy": "#FFC09F", "Calm": "#95D5B2", "Excited": "#D96C9D", "Grateful": "#F8A5C2",
    "Tired": "#CDB4DB", "Stressed": "#9D8AC7", "Sad": "#A9C5E8", "Overwhelmed": "#E6D9F2",
}


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

def esc(text):
    """Make user text safe for HTML and keep line breaks."""
    return html.escape(str(text or "")).replace("\n", "<br>")


def card(body_html, tone="white"):
    st.markdown(f'<div class="hs-card hs-{tone}">{body_html}</div>', unsafe_allow_html=True)


def page_header(emoji, title, subtitle):
    st.markdown(
        f'<div class="hs-page-header"><h2>{emoji} {esc(title)}</h2><p>{esc(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )
    show_flash()


def empty_state(emoji, title, text):
    st.markdown(
        f'<div class="hs-empty"><div class="big">{emoji}</div><h4>{esc(title)}</h4>'
        f'<p>{esc(text)}</p></div>',
        unsafe_allow_html=True,
    )


def flash(message):
    """Remember a success message to show after the page reloads."""
    st.session_state["flash_message"] = message


def show_flash():
    message = st.session_state.pop("flash_message", None)
    if message:
        st.success(message, icon="🎀")


def run_ai(spinner_text, function, *args):
    """
    Call an ai_service function safely.
    Returns the result, or None after showing a friendly message.
    """
    if not ai.is_configured():
        st.info(ai.NO_KEY_MESSAGE, icon="🔑")
        return None
    try:
        with st.spinner(spinner_text):
            return function(*args)
    except ai.AIError as error:
        st.error(str(error), icon="🌧️")
        return None


def mood_emoji(name):
    return db.MOOD_OPTIONS.get(name, "")


def date_or_none(text):
    return date.fromisoformat(text) if text else None


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------

def home_page():
    today = date.today()
    st.markdown(
        f'<div class="hs-hero"><div class="hs-title">🌸 HerSpace AI 🌸</div>'
        f'<div class="hs-tagline">{TAGLINE}</div>'
        f'<div class="hs-welcome">Welcome back, lovely! ✨ Today is {today:%A, %d %B %Y}</div></div>',
        unsafe_allow_html=True,
    )
    show_flash()

    if not db.has_any_data():
        card(
            "<h4>🌷 Let's get you started</h4>"
            "<p>Your space is empty for now, and that's perfectly okay. Try one of these:</p>"
            "<p>📔 Write your first journal entry &nbsp;•&nbsp; 🌸 Check in with your mood &nbsp;•&nbsp; "
            "✨ Add a habit &nbsp;•&nbsp; 🎯 Dream up a goal</p>"
            "<p class='hs-small'>Use the menu on the left. Everything you save will appear here.</p>",
            "peach",
        )

    # Daily affirmation
    affirmation = ai.LOCAL_AFFIRMATIONS[today.toordinal() % len(ai.LOCAL_AFFIRMATIONS)]
    card(f"<div class='hs-quote'>💖 {esc(affirmation)}</div>", "lavender")

    left, right = st.columns(2)

    with left:
        st.subheader("📝 Today's tasks")
        routines = db.get_routines_due(today)
        done_routines = db.get_done_routine_ids(today)
        habits = [h for h in db.get_habits() if db.habit_is_due_on(h, today)]
        done_habits = db.get_done_habit_ids(today)
        todo = [f"🧴 {r['name']}" for r in routines if r["id"] not in done_routines]
        todo += [f"✨ {h['name']}" for h in habits if h["id"] not in done_habits]
        if not routines and not habits:
            empty_state("🌼", "No tasks yet", "Add self-care routines or habits and they will show up here.")
        elif not todo:
            card("<h4>🎉 All done for today!</h4><p>Every routine and habit is checked off.</p>", "mint")
        else:
            body = "".join(f"<p>• {esc(item)}</p>" for item in todo)
            card(f"<h4>Still to do</h4>{body}", "white")

    with right:
        st.subheader("🌸 Mood check-in")
        today_moods = db.get_moods(today, today)
        if today_moods:
            latest = today_moods[0]["mood"]
            card(f"<h4>{mood_emoji(latest)} You logged feeling {esc(latest.lower())} today</h4>"
                 "<p class='hs-small'>You can add another check-in anytime.</p>", "pink")
        with st.form("home_mood_form", clear_on_submit=True):
            choice = st.selectbox("How are you feeling right now?", list(MOOD_LABELS))
            if st.form_submit_button("Save check-in"):
                db.add_mood(today, MOOD_LABELS[choice])
                flash("Mood saved. Thank you for checking in! 💗")
                st.rerun()

    st.subheader("🎯 Active goals")
    goals = db.get_goals(active_only=True)
    if not goals:
        empty_state("🎯", "No active goals", "Create a goal on the My Goals page and track it here.")
    for goal in goals[:4]:
        st.markdown(f"**{goal['title']}** — {goal['progress']}%")
        st.progress(goal["progress"] / 100)

    st.subheader("✨ Habit summary")
    all_habits = [h for h in db.get_habits() if db.habit_is_due_on(h, today)]
    if not all_habits:
        empty_state("✨", "No habits yet", "Add a habit on the Habit Tracker page to see your daily summary.")
    else:
        done = db.get_done_habit_ids(today)
        count = sum(1 for h in all_habits if h["id"] in done)
        st.markdown(f"**{count} of {len(all_habits)}** habits completed today")
        st.progress(count / len(all_habits))

    st.subheader("💫 Quick access")
    links = [("journal", "📔", "My Journal", "Write freely"), ("mood", "🌸", "Mood Tracker", "Check in"),
             ("selfcare", "🧴", "Self-Care", "Plan your routines"), ("goals", "🎯", "My Goals", "Plan with AI"),
             ("habits", "✨", "Habits", "Build consistency"), ("affirmations", "💖", "Affirmations", "Feel encouraged"),
             ("bestie", "🤖", "AI Bestie", "Chat and plan")]
    tones = ["pink", "lavender", "peach", "mint"]
    columns = st.columns(4)
    for index, (key, emoji, title, text) in enumerate(links):
        with columns[index % 4]:
            card(f"<h4>{emoji} {title}</h4><p class='hs-small'>{text}</p>", tones[index % 4])
            if key in PAGES:
                st.page_link(PAGES[key], label=f"Open {title}", icon=emoji)

    st.subheader("🕰️ Recent activity")
    recent = db.get_recent_activity(6)
    if not recent:
        empty_state("🕰️", "Nothing here yet", "Your latest journal entries, moods, habits and goals will appear here.")
    for item in recent:
        st.markdown(f"- {item['text']}  \n  <span class='hs-small'>{item['ts'].replace('T', ' ')}</span>",
                    unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------

def journal_page():
    page_header("📔", "My Journal", "A soft place for your thoughts. Entries only go to AI when you click an AI button.")
    tab_write, tab_entries, tab_prompts = st.tabs(["✍️ Write", "📚 My entries", "💡 Prompts"])
    mood_choices = ["(no mood)"] + list(MOOD_LABELS)

    with tab_write:
        with st.form("new_journal_entry", clear_on_submit=True):
            title = st.text_input("Title (optional)")
            col1, col2 = st.columns(2)
            entry_date = col1.date_input("Date", value=date.today())
            mood_choice = col2.selectbox("Mood", mood_choices)
            content = st.text_area("Dear diary...", height=240)
            saved = st.form_submit_button("💾 Save entry")
        if saved:
            try:
                mood = MOOD_LABELS.get(mood_choice, "")
                db.add_journal_entry(title, content, entry_date, mood)
                flash("Your entry is safely saved. 📔")
                st.rerun()
            except ValueError as error:
                st.error(str(error))

    with tab_entries:
        search = st.text_input("🔍 Search your entries", key="journal_search")
        entries = db.get_journal_entries(search)
        if not entries:
            if search.strip():
                empty_state("🔍", "No matches", "Try a different word.")
            else:
                empty_state("📔", "Your diary is waiting", "Write your first entry in the Write tab.")
        st.caption("🔒 AI actions send only the one entry you click, and only when you click.")
        for entry in entries:
            _journal_entry_block(entry, mood_choices)

    with tab_prompts:
        topic = st.text_input("Anything you'd like prompts about? (optional)")
        if st.button("✨ Get journaling prompts"):
            if ai.is_configured():
                result = run_ai("Thinking up prompts...", ai.journaling_prompts, topic)
            else:
                st.info("Gemini is not set up, so here are some prompts from my local collection.", icon="🌷")
                result = "\n".join(f"{i}. {p}" for i, p in
                                   enumerate(random.sample(ai.LOCAL_JOURNAL_PROMPTS, 5), start=1))
            if result:
                st.session_state["journal_prompts"] = result
        if st.session_state.get("journal_prompts"):
            card(esc(st.session_state["journal_prompts"]), "lavender")


def _journal_entry_block(entry, mood_choices):
    entry_id = entry["id"]
    title = entry["title"] or "Untitled"
    label = f"{entry['entry_date']} · {title} {mood_emoji(entry['mood'])}"
    with st.expander(label):
        card(esc(entry["content"]), "pink")

        col1, col2 = st.columns(2)
        if col1.button("🪞 Reflect on this entry", key=f"reflect_{entry_id}"):
            result = run_ai("Reflecting...", ai.reflect_on_entry, entry["title"], entry["content"], entry["mood"])
            if result:
                st.session_state[f"reflection_{entry_id}"] = result
        if col2.button("📝 Short summary", key=f"summary_{entry_id}"):
            result = run_ai("Summarizing...", ai.summarize_entry, entry["title"], entry["content"])
            if result:
                st.session_state[f"summary_{entry_id}"] = result
        if st.session_state.get(f"reflection_{entry_id}"):
            st.markdown("**🪞 Reflection**")
            card(esc(st.session_state[f"reflection_{entry_id}"]), "lavender")
        if st.session_state.get(f"summary_{entry_id}"):
            st.markdown("**📝 Summary**")
            card(esc(st.session_state[f"summary_{entry_id}"]), "mint")

        if st.checkbox("✏️ Edit this entry", key=f"edit_toggle_{entry_id}"):
            with st.form(f"edit_entry_{entry_id}"):
                new_title = st.text_input("Title", value=entry["title"])
                new_date = st.date_input("Date", value=date.fromisoformat(entry["entry_date"]))
                current = next((k for k, v in MOOD_LABELS.items() if v == entry["mood"]), "(no mood)")
                new_mood = st.selectbox("Mood", mood_choices, index=mood_choices.index(current))
                new_content = st.text_area("Entry", value=entry["content"], height=200)
                if st.form_submit_button("💾 Save changes"):
                    try:
                        db.update_journal_entry(entry_id, new_title, new_content, new_date,
                                                MOOD_LABELS.get(new_mood, ""))
                        flash("Entry updated. ✨")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        confirm = st.checkbox("I am sure I want to delete this entry", key=f"confirm_del_{entry_id}")
        if st.button("🗑️ Delete entry", key=f"del_{entry_id}"):
            if confirm:
                db.delete_journal_entry(entry_id)
                flash("Entry deleted.")
                st.rerun()
            else:
                st.warning("Please tick the box first to confirm.")


# --------------------------------------------------------------------------
# Mood tracker
# --------------------------------------------------------------------------

def mood_page():
    page_header("🌸", "Mood Tracker", "Notice how you feel over time. This is a gentle diary, not a medical assessment.")
    today = date.today()

    with st.form("new_mood", clear_on_submit=True):
        col1, col2 = st.columns(2)
        mood_date = col1.date_input("Date", value=today)
        mood_choice = col2.selectbox("How are you feeling?", list(MOOD_LABELS))
        note = st.text_input("Add a note (optional)")
        if st.form_submit_button("💗 Save mood"):
            db.add_mood(mood_date, MOOD_LABELS[mood_choice], note)
            flash("Mood saved. 🌸")
            st.rerun()

    st.subheader("📅 This week")
    week_start = today - timedelta(days=6)
    week = db.get_moods(week_start, today)
    if not week:
        empty_state("🌸", "No moods this week", "Save a mood above and your weekly summary will appear.")
    else:
        counts = pd.Series([m["mood"] for m in week]).value_counts()
        top = counts.index[0]
        card(f"<h4>{mood_emoji(top)} Most common mood: {esc(top)}</h4>"
             f"<p>{len(week)} check-in(s) in the last 7 days.</p>", "pink")
        columns = st.columns(7)
        for offset, column in enumerate(columns):
            day = week_start + timedelta(days=offset)
            day_moods = [m for m in week if m["mood_date"] == day.isoformat()]
            emojis = " ".join(mood_emoji(m["mood"]) for m in day_moods) or "·"
            column.markdown(f'<div class="hs-daycell"><div class="emoji">{emojis}</div>'
                            f'<div class="hs-small">{day:%a}<br>{day:%d}</div></div>', unsafe_allow_html=True)

    st.subheader("🔎 History")
    chosen = st.date_input("Filter by date", value=(today - timedelta(days=29), today), key="mood_filter")
    if isinstance(chosen, (tuple, list)):
        start = chosen[0]
        end = chosen[1] if len(chosen) > 1 else chosen[0]
    else:
        start = end = chosen
    records = db.get_moods(start, end)

    if not records:
        empty_state("💭", "No moods in this range", "Pick a different range or save a new mood.")
        return

    frame = pd.DataFrame(records)
    distribution = frame.groupby("mood").size().reset_index(name="count")
    figure = px.pie(distribution, names="mood", values="count", hole=0.5,
                    color="mood", color_discrete_map=MOOD_COLORS, title="Mood distribution")
    figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color=PALETTE["plum"])
    st.plotly_chart(figure)

    for record in records:
        label = f"{record['mood_date']} · {mood_emoji(record['mood'])} {record['mood']}"
        with st.expander(label):
            if record["note"]:
                card(esc(record["note"]), "lavender")
            with st.form(f"edit_mood_{record['id']}"):
                new_date = st.date_input("Date", value=date.fromisoformat(record["mood_date"]))
                current = next(k for k, v in MOOD_LABELS.items() if v == record["mood"])
                new_mood = st.selectbox("Mood", list(MOOD_LABELS), index=list(MOOD_LABELS).index(current))
                new_note = st.text_input("Note", value=record["note"])
                if st.form_submit_button("💾 Save changes"):
                    db.update_mood(record["id"], new_date, MOOD_LABELS[new_mood], new_note)
                    flash("Mood updated.")
                    st.rerun()
            confirm = st.checkbox("I want to delete this mood", key=f"confirm_mood_{record['id']}")
            if st.button("🗑️ Delete", key=f"del_mood_{record['id']}"):
                if confirm:
                    db.delete_mood(record["id"])
                    flash("Mood deleted.")
                    st.rerun()
                else:
                    st.warning("Please tick the box first to confirm.")


# --------------------------------------------------------------------------
# Self-care planner
# --------------------------------------------------------------------------

CATEGORY_EMOJI = {"Skincare": "🧴", "Haircare": "💇‍♀️", "Relaxation": "🛁", "Reading": "📖",
                  "Personal care": "🪞", "Hobbies": "🎨", "Other": "🌼"}


def _toggle_routine(routine_id, day, key):
    db.set_routine_done(routine_id, day, st.session_state[key])


def selfcare_page():
    page_header("🧴", "Self-Care Planner", "Small, kind routines for a softer day. Be gentle with yourself.")
    today = date.today()
    tab_today, tab_manage, tab_history, tab_ideas = st.tabs(
        ["🌤️ Today", "🗂️ My routines", "📈 History", "💡 Ideas"])

    with tab_today:
        due = db.get_routines_due(today)
        if not due:
            empty_state("🌤️", "Nothing planned for today", "Add a routine in the My routines tab.")
        done = db.get_done_routine_ids(today)
        for routine in due:
            key = f"routine_{routine['id']}_{today}"
            st.checkbox(f"{CATEGORY_EMOJI.get(routine['category'], '🌼')} {routine['name']}",
                        value=routine["id"] in done, key=key,
                        on_change=_toggle_routine, args=(routine["id"], today, key),
                        help=routine["description"] or None)
        if due and all(r["id"] in done for r in due):
            card("<h4>🎉 You did it!</h4><p>All of today's routines are complete.</p>", "mint")

    with tab_manage:
        st.subheader("➕ Add a routine")
        with st.form("new_routine", clear_on_submit=True):
            name = st.text_input("Routine name")
            description = st.text_area("Description (optional)", height=80)
            col1, col2, col3 = st.columns(3)
            category = col1.selectbox("Category", db.SELFCARE_CATEGORIES)
            frequency = col2.selectbox("Frequency", db.SELFCARE_FREQUENCIES)
            weekday = col3.selectbox("Day (used for Weekly)", db.WEEKDAY_NAMES)
            if st.form_submit_button("🌷 Add routine"):
                try:
                    db.add_routine(name, description, category, frequency, weekday)
                    flash("Routine added. 🧴")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

        routines = db.get_routines()
        if not routines:
            empty_state("🧴", "No routines yet", "Add your first routine above.")
        for routine in routines:
            when = routine["frequency"] + (f" ({routine['schedule_day']})" if routine["schedule_day"] else "")
            with st.expander(f"{CATEGORY_EMOJI.get(routine['category'], '🌼')} {routine['name']} · {when}"):
                if routine["description"]:
                    card(esc(routine["description"]), "peach")
                with st.form(f"edit_routine_{routine['id']}"):
                    new_name = st.text_input("Name", value=routine["name"])
                    new_desc = st.text_area("Description", value=routine["description"], height=80)
                    col1, col2, col3 = st.columns(3)
                    new_cat = col1.selectbox("Category", db.SELFCARE_CATEGORIES,
                                             index=db.SELFCARE_CATEGORIES.index(routine["category"]))
                    new_freq = col2.selectbox("Frequency", db.SELFCARE_FREQUENCIES,
                                              index=db.SELFCARE_FREQUENCIES.index(routine["frequency"]))
                    day_index = db.WEEKDAY_NAMES.index(routine["schedule_day"]) if routine["schedule_day"] else 0
                    new_day = col3.selectbox("Day (Weekly)", db.WEEKDAY_NAMES, index=day_index)
                    if st.form_submit_button("💾 Save changes"):
                        try:
                            db.update_routine(routine["id"], new_name, new_desc, new_cat, new_freq, new_day)
                            flash("Routine updated.")
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
                confirm = st.checkbox("I want to delete this routine", key=f"confirm_routine_{routine['id']}")
                if st.button("🗑️ Delete", key=f"del_routine_{routine['id']}"):
                    if confirm:
                        db.delete_routine(routine["id"])
                        flash("Routine deleted.")
                        st.rerun()
                    else:
                        st.warning("Please tick the box first to confirm.")

    with tab_history:
        history = db.get_routine_history(30)
        if not history:
            empty_state("📈", "No history yet", "Tick off a routine on the Today tab and it will appear here.")
        else:
            frame = pd.DataFrame(history).rename(
                columns={"completed_date": "Date", "name": "Routine", "category": "Category"})
            st.caption("Completed routines in the last 30 days")
            st.dataframe(frame, hide_index=True)

    with tab_ideas:
        st.caption("Gemini gives general ideas only. It is not medical or beauty advice.")
        focus = st.text_input("What would you like ideas for? (optional)", key="selfcare_focus")
        if st.button("✨ Ask Gemini for self-care ideas"):
            result = run_ai("Gathering gentle ideas...", ai.selfcare_suggestions, focus)
            if result:
                st.session_state["selfcare_ideas"] = result
        if st.session_state.get("selfcare_ideas"):
            card(esc(st.session_state["selfcare_ideas"]), "mint")


# --------------------------------------------------------------------------
# Goals
# --------------------------------------------------------------------------

def _toggle_milestone(milestone_id, key):
    db.set_milestone_done(milestone_id, st.session_state[key])


def _create_plan(goal):
    """Ask Gemini for a plan and save it. The goal itself is already saved."""
    plan = run_ai("Planning your goal...", ai.goal_plan, goal["title"], goal["description"],
                  goal["progress"], goal["available_time"], goal["target_date"], goal["preferences"])
    if plan:
        db.save_goal_plan(goal["id"], plan)
        flash("Your plan is ready! 🌟")
        return True
    return False


def goals_page():
    page_header("🎯", "My Goals", "Turn big dreams into small, doable steps with a little help from AI.")
    tab_new, tab_goals = st.tabs(["🌟 New goal", "🎯 My goals"])

    with tab_new:
        with st.form("new_goal", clear_on_submit=True):
            title = st.text_input("Goal title")
            description = st.text_area("Goal description", height=100)
            col1, col2 = st.columns(2)
            progress = col1.slider("Current progress (%)", 0, 100, 0)
            available_time = col2.text_input("Available time", placeholder="e.g. 30 minutes a day")
            use_target = st.checkbox("Set a target date")
            target = st.date_input("Target date", value=date.today() + timedelta(days=30))
            preferences = st.text_area("Personal preferences (optional)", height=80,
                                       placeholder="e.g. I like short sessions, I study best in the evening")
            save_only = st.form_submit_button("💾 Save goal")
            save_plan = st.form_submit_button("✨ Save goal and create AI plan")
        if save_only or save_plan:
            try:
                goal_id = db.add_goal(title, description, progress, available_time,
                                      target if use_target else None, preferences)
            except ValueError as error:
                st.error(str(error))
            else:
                if save_plan and not _create_plan(db.get_goal(goal_id)):
                    st.warning("Your goal was saved, so nothing is lost. "
                               "You can create the AI plan later from the My goals tab.")
                else:
                    flash("Goal saved. 🎯")
                    st.rerun()

    with tab_goals:
        goals = db.get_goals()
        if not goals:
            empty_state("🎯", "No goals yet", "Add your first goal in the New goal tab.")
        for goal in goals:
            _goal_block(goal)


def _goal_block(goal):
    goal_id = goal["id"]
    icon = "🏆" if goal["progress"] >= 100 else "🎯"
    with st.expander(f"{icon} {goal['title']} — {goal['progress']}%"):
        st.progress(goal["progress"] / 100)
        details = []
        if goal["description"]:
            details.append(esc(goal["description"]))
        if goal["target_date"]:
            details.append(f"📅 Target date: {esc(goal['target_date'])}")
        if goal["available_time"]:
            details.append(f"⏰ Time available: {esc(goal['available_time'])}")
        if details:
            card("<p>" + "</p><p>".join(details) + "</p>", "peach")

        with st.form(f"progress_form_{goal_id}"):
            new_progress = st.slider("Update progress (%)", 0, 100, value=goal["progress"])
            if st.form_submit_button("📈 Save progress"):
                db.update_goal_progress(goal_id, new_progress)
                flash("Progress updated. Keep glowing! ✨" if new_progress < 100 else "Goal complete! 🏆")
                st.rerun()

        label = "🔄 Regenerate AI plan" if goal["plan_json"] else "✨ Create AI plan"
        if st.button(label, key=f"plan_{goal_id}"):
            if _create_plan(goal):
                st.rerun()
        if goal["plan_json"]:
            _show_plan(goal)

        if st.checkbox("✏️ Edit this goal", key=f"edit_goal_toggle_{goal_id}"):
            with st.form(f"edit_goal_{goal_id}"):
                new_title = st.text_input("Title", value=goal["title"])
                new_desc = st.text_area("Description", value=goal["description"], height=100)
                col1, col2 = st.columns(2)
                new_prog = col1.slider("Progress (%)", 0, 100, value=goal["progress"])
                new_time = col2.text_input("Available time", value=goal["available_time"])
                has_target = st.checkbox("Has a target date", value=bool(goal["target_date"]))
                new_target = st.date_input("Target date", value=date_or_none(goal["target_date"])
                                           or date.today() + timedelta(days=30))
                new_prefs = st.text_area("Preferences", value=goal["preferences"], height=80)
                if st.form_submit_button("💾 Save changes"):
                    try:
                        db.update_goal(goal_id, new_title, new_desc, new_prog, new_time,
                                       new_target if has_target else None, new_prefs)
                        flash("Goal updated.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        confirm = st.checkbox("I want to delete this goal", key=f"confirm_goal_{goal_id}")
        if st.button("🗑️ Delete goal", key=f"del_goal_{goal_id}"):
            if confirm:
                db.delete_goal(goal_id)
                flash("Goal deleted.")
                st.rerun()
            else:
                st.warning("Please tick the box first to confirm.")


def _show_plan(goal):
    try:
        plan = json.loads(goal["plan_json"])
    except json.JSONDecodeError:
        st.warning("The saved plan could not be read. Try regenerating it.")
        return
    st.markdown("### 🌟 Your plan")
    if plan.get("summary"):
        card(f"<h4>Summary</h4><p>{esc(plan['summary'])}</p>", "lavender")
    if plan.get("steps"):
        st.markdown("**Action steps**")
        for number, step in enumerate(plan["steps"], start=1):
            st.markdown(f"{number}. {step}")
    if plan.get("timeline"):
        card(f"<h4>🗓️ Suggested timeline</h4><p>{esc(plan['timeline'])}</p>", "peach")
    if plan.get("weekly_milestones"):
        st.markdown("**Weekly milestones**")
        tones = ["pink", "lavender", "mint", "peach"]
        for index, milestone in enumerate(plan["weekly_milestones"]):
            card(f"<p>🌸 {esc(milestone)}</p>", tones[index % 4])
    milestones = db.get_milestones(goal["id"])
    if milestones:
        st.markdown("**✅ Checklist**")
        for item in milestones:
            key = f"milestone_{item['id']}"
            st.checkbox(item["title"], value=bool(item["is_done"]), key=key,
                        on_change=_toggle_milestone, args=(item["id"], key))
    if plan.get("encouragement"):
        card(f"<p>💖 {esc(plan['encouragement'])}</p>", "pink")
    st.caption("AI plans are suggestions. Adjust them so they fit your real life.")


# --------------------------------------------------------------------------
# Habits
# --------------------------------------------------------------------------

def _toggle_habit(habit_id, day, key):
    db.set_habit_done(habit_id, day, st.session_state[key])


def habits_page():
    page_header("✨", "Habit Tracker", "Tiny actions, repeated. Every check-in counts.")
    today = date.today()
    tab_today, tab_manage, tab_progress = st.tabs(["🌤️ Today", "🗂️ My habits", "📊 Progress"])

    with tab_today:
        habits = [h for h in db.get_habits() if db.habit_is_due_on(h, today)]
        if not habits:
            empty_state("✨", "No habits for today", "Add a habit in the My habits tab.")
        done = db.get_done_habit_ids(today)
        for habit in habits:
            key = f"habit_{habit['id']}_{today}"
            st.checkbox(habit["name"], value=habit["id"] in done, key=key,
                        on_change=_toggle_habit, args=(habit["id"], today, key),
                        help=habit["description"] or None)
            streak = db.get_habit_stats(habit["id"], today)["streak"]
            if streak > 0:
                st.caption(f"🔥 {streak}-day streak")
        if habits and all(h["id"] in done for h in habits):
            card("<h4>🎉 Habits complete!</h4><p>Everything is checked off for today.</p>", "mint")

    with tab_manage:
        st.subheader("➕ Add a habit")
        st.caption("Ideas: Practice Python, Read for 15 minutes, Write in my journal, Organize my daily tasks.")
        with st.form("new_habit", clear_on_submit=True):
            name = st.text_input("Habit name")
            description = st.text_area("Description (optional)", height=80)
            frequency = st.selectbox("Frequency", db.HABIT_FREQUENCIES)
            if st.form_submit_button("🌱 Add habit"):
                try:
                    db.add_habit(name, description, frequency)
                    flash("Habit added. 🌱")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
        habits = db.get_habits()
        if not habits:
            empty_state("🌱", "No habits yet", "Add your first habit above.")
        for habit in habits:
            with st.expander(f"✨ {habit['name']} · {habit['frequency']}"):
                if habit["description"]:
                    card(esc(habit["description"]), "lavender")
                with st.form(f"edit_habit_{habit['id']}"):
                    new_name = st.text_input("Name", value=habit["name"])
                    new_desc = st.text_area("Description", value=habit["description"], height=80)
                    new_freq = st.selectbox("Frequency", db.HABIT_FREQUENCIES,
                                            index=db.HABIT_FREQUENCIES.index(habit["frequency"]))
                    if st.form_submit_button("💾 Save changes"):
                        try:
                            db.update_habit(habit["id"], new_name, new_desc, new_freq)
                            flash("Habit updated.")
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
                confirm = st.checkbox("I want to delete this habit and its history",
                                      key=f"confirm_habit_{habit['id']}")
                if st.button("🗑️ Delete", key=f"del_habit_{habit['id']}"):
                    if confirm:
                        db.delete_habit(habit["id"])
                        flash("Habit deleted.")
                        st.rerun()
                    else:
                        st.warning("Please tick the box first to confirm.")

    with tab_progress:
        habits = db.get_habits()
        history = db.get_habit_history(30)
        if not habits or not history:
            empty_state("📊", "No progress to show yet",
                        "Check off a habit on the Today tab and your stats will appear here.")
        else:
            rows = []
            for habit in habits:
                stats = db.get_habit_stats(habit["id"], today)
                rows.append({"Habit": habit["name"], "Frequency": habit["frequency"],
                             "Total check-ins": stats["total"], "Last 7 days": stats["last_7_days"],
                             "Last 30 days": stats["last_30_days"], "Current streak (days)": stats["streak"]})
            stats_frame = pd.DataFrame(rows)
            st.dataframe(stats_frame, hide_index=True)

            daily = pd.DataFrame(db.get_habit_daily_counts(14))
            figure = px.bar(daily, x="date", y="completed", title="Habits completed per day (last 14 days)",
                            color_discrete_sequence=[PALETTE["rose"]])
            figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.6)",
                                 font_color=PALETTE["plum"], xaxis_title="", yaxis_title="Completed")
            figure.update_yaxes(dtick=1)
            st.plotly_chart(figure)

            figure2 = px.bar(stats_frame, x="Habit", y="Last 30 days", title="Check-ins per habit (last 30 days)",
                             color_discrete_sequence=[PALETTE["pastel_purple"]])
            figure2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.6)",
                                  font_color=PALETTE["plum"])
            st.plotly_chart(figure2)

            st.markdown("**Completion history (last 30 days)**")
            st.dataframe(pd.DataFrame(history).rename(columns={"completed_date": "Date", "name": "Habit"}),
                         hide_index=True)


# --------------------------------------------------------------------------
# Affirmations
# --------------------------------------------------------------------------

def affirmations_page():
    page_header("💖", "Daily Affirmations", "Kind words, realistic and gentle. Save the ones that feel like you.")
    if "current_affirmation" not in st.session_state:
        st.session_state["current_affirmation"] = ai.LOCAL_AFFIRMATIONS[
            date.today().toordinal() % len(ai.LOCAL_AFFIRMATIONS)]
    current = st.session_state["current_affirmation"]
    card(f"<div class='hs-quote'>💖 {esc(current)}</div>", "pink")

    col1, col2, col3 = st.columns(3)
    if col1.button("🔄 Another one"):
        choices = [a for a in ai.LOCAL_AFFIRMATIONS if a != current]
        st.session_state["current_affirmation"] = random.choice(choices)
        st.rerun()
    if col2.button("🤖 New one from Gemini"):
        if ai.is_configured():
            new_text = run_ai("Writing something kind...", ai.new_affirmation)
            if new_text:
                st.session_state["current_affirmation"] = new_text
                st.rerun()
        else:
            st.info("Gemini is not set up, so I picked one from my local collection instead.", icon="🌷")
            st.session_state["current_affirmation"] = random.choice(
                [a for a in ai.LOCAL_AFFIRMATIONS if a != current])
            st.rerun()
    if db.is_favorite(current):
        col3.button("💗 Already in favorites", disabled=True)
    elif col3.button("💗 Save to favorites"):
        db.add_favorite(current)
        flash("Saved to your favorites. 💗")
        st.rerun()

    st.subheader("💗 My favorites")
    favorites = db.get_favorites()
    if not favorites:
        empty_state("💗", "No favorites yet", "Tap “Save to favorites” on an affirmation you love.")
    for favorite in favorites:
        card(f"<p>💖 {esc(favorite['text'])}</p>", "lavender")
        if st.button("Remove", key=f"remove_fav_{favorite['id']}"):
            db.remove_favorite(favorite["id"])
            flash("Removed from favorites.")
            st.rerun()


# --------------------------------------------------------------------------
# AI Bestie
# --------------------------------------------------------------------------

def bestie_page():
    page_header("🤖", "AI Bestie", "A friendly helper for planning your day, study sessions, goals and next steps.")
    st.caption("I'm an AI, not a person, therapist or doctor. I only see what you type in this chat, "
               "and the chat disappears when you close the app unless you copy it somewhere.")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    history = st.session_state["chat_history"]

    if not ai.is_configured():
        st.info(ai.NO_KEY_MESSAGE, icon="🔑")

    if st.button("🧹 Clear chat"):
        st.session_state["chat_history"] = []
        flash("Chat cleared.")
        st.rerun()

    if not history:
        card("<h4>Hi, I'm your AI Bestie! 🌷</h4>"
             "<p>Try: “Help me plan my study session for tomorrow”, “Turn these tasks into a to-do list”, "
             "or “Give me a journaling prompt about change”.</p>", "lavender")

    for message in history:
        avatar = "🌸" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    prompt = st.chat_input("Tell me what's on your mind...", disabled=not ai.is_configured())
    if prompt:
        with st.chat_message("user", avatar="🌸"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            reply = run_ai("Thinking...", ai.chat_reply, history, prompt)
            if reply:
                st.markdown(reply)
        history.append({"role": "user", "content": prompt})
        if reply:
            history.append({"role": "assistant", "content": reply})


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------

def settings_page():
    page_header("⚙️", "Settings", "Information about the app, plus your data controls.")

    st.subheader("🎨 Theme")
    card("<p>HerSpace AI uses one soft pastel theme (baby pink, lavender, peach, mint and dark plum). "
         "Theme switching is not included in this version, so there are no fake theme buttons.</p>", "lavender")

    st.subheader("ℹ️ About this app")
    ai_status = "connected ✅" if ai.is_configured() else "not configured (AI features are off)"
    card(f"<p><b>HerSpace AI</b> version {APP_VERSION}</p><p>{TAGLINE}</p>"
         f"<p>Gemini: {ai_status}<br>Model: {esc(ai.get_model_name())}</p>"
         "<p class='hs-small'>This first version is a single-user app with no login. "
         "Do not share one running copy between several people.</p>", "peach")

    st.subheader("🔒 Privacy")
    st.markdown(
        "- Your data is saved in a local SQLite file, not sent anywhere automatically.\n"
        "- Text goes to Gemini only when you click an AI button or send a chat message.\n"
        "- If you deploy on Streamlit Community Cloud, saved data may be erased when the app restarts. "
        "Export your data regularly."
    )

    st.subheader("🧹 Chat history")
    if st.button("Clear AI Bestie chat"):
        st.session_state["chat_history"] = []
        flash("Chat history cleared.")
        st.rerun()

    st.subheader("📦 Export my data")
    export_json = json.dumps(db.export_all_data(), ensure_ascii=False, indent=2, default=str)
    st.download_button("⬇️ Download everything (JSON)", data=export_json,
                       file_name=f"herspace-export-{date.today()}.json", mime="application/json")

    st.subheader("🗑️ Delete my data")
    st.warning("This permanently deletes your journal, moods, routines, goals, habits and favorites.")
    typed = st.text_input("Type DELETE to confirm", key="delete_confirm_text")
    if st.button("Delete all my data"):
        if typed.strip() == "DELETE":
            db.delete_all_data()
            st.session_state.pop("delete_confirm_text", None)
            flash("All saved data was deleted.")
            st.rerun()
        else:
            st.error("Please type DELETE (in capital letters) first.")
