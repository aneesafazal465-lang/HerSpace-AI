"""
app.py - the starting point of HerSpace AI.

Run it with:  streamlit run app.py
It sets up the page, the database, the styling and the sidebar navigation.
The page content itself lives in views.py.
"""

import streamlit as st

import database as db
import views
from styles import apply_styles

st.set_page_config(
    page_title="HerSpace AI",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def setup_database():
    """Create the tables once per server start."""
    db.init_db()
    return True


setup_database()
apply_styles()

# Each st.Page connects a sidebar item to a function in views.py.
pages = {
    "home": st.Page(views.home_page, title="Home", icon="🏠", default=True),
    "journal": st.Page(views.journal_page, title="My Journal", icon="📔"),
    "mood": st.Page(views.mood_page, title="Mood Tracker", icon="🌸"),
    "selfcare": st.Page(views.selfcare_page, title="Self-Care Planner", icon="🧴"),
    "goals": st.Page(views.goals_page, title="My Goals", icon="🎯"),
    "habits": st.Page(views.habits_page, title="Habit Tracker", icon="✨"),
    "affirmations": st.Page(views.affirmations_page, title="Daily Affirmations", icon="💖"),
    "bestie": st.Page(views.bestie_page, title="AI Bestie", icon="🤖"),
    "settings": st.Page(views.settings_page, title="Settings", icon="⚙️"),
}
views.PAGES.update(pages)

navigation = st.navigation(list(pages.values()))

with st.sidebar:
    st.markdown("### 🌸 HerSpace AI")
    st.caption("Your little corner to grow, glow, and become your best self.")

navigation.run()
