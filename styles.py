"""
styles.py - the colors and custom CSS for HerSpace AI.

If the CSS ever fails to load, the app still works, it just looks plainer.
"""

import streamlit as st

PALETTE = {
    "baby_pink": "#F8C8DC",
    "lavender": "#E6D9F2",
    "pastel_purple": "#CDB4DB",
    "rose": "#D96C9D",
    "peach": "#FFD6C2",
    "cream": "#FFF9F5",
    "mint": "#D8F3DC",
    "white": "#FFFFFF",
    "plum": "#443642",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
  --pink: #F8C8DC; --lavender: #E6D9F2; --purple: #CDB4DB; --rose: #D96C9D;
  --peach: #FFD6C2; --cream: #FFF9F5; --mint: #D8F3DC; --white: #FFFFFF; --plum: #443642;
}

html, body, [class*="css"], .stApp {
  font-family: 'Nunito', 'Segoe UI', sans-serif;
  color: var(--plum);
}
[data-testid="stAppViewContainer"] {
  background: linear-gradient(160deg, #FFF9F5 0%, #FBE9F1 45%, #EFE6F8 100%);
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #F8C8DC 0%, #E6D9F2 60%, #FFF9F5 100%);
}
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1100px; }

h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; color: var(--plum); }

/* ---------- hero ---------- */
.hs-hero {
  background: linear-gradient(135deg, #F8C8DC 0%, #CDB4DB 55%, #E6D9F2 100%);
  border-radius: 28px; padding: 2.4rem 2rem; margin-bottom: 1.6rem; text-align: center;
  box-shadow: 0 10px 30px rgba(217, 108, 157, 0.25);
}
.hs-title {
  font-family: 'Playfair Display', Georgia, serif; font-size: 3.2rem; font-weight: 700;
  color: var(--plum); line-height: 1.1;
}
.hs-tagline { font-size: 1.15rem; margin-top: .5rem; color: var(--plum); font-style: italic; }
.hs-welcome { margin-top: 1rem; font-weight: 700; color: #7a3e5c; }

/* ---------- page header ---------- */
.hs-page-header {
  background: linear-gradient(120deg, #F8C8DC, #E6D9F2);
  border-radius: 22px; padding: 1.3rem 1.6rem; margin-bottom: 1.4rem;
  box-shadow: 0 6px 18px rgba(205, 180, 219, 0.35);
}
.hs-page-header h2 { margin: 0; font-size: 1.9rem; }
.hs-page-header p { margin: .3rem 0 0 0; opacity: .85; }

/* ---------- cards ---------- */
.hs-card {
  border-radius: 20px; padding: 1.1rem 1.3rem; margin: .5rem 0 1rem 0;
  box-shadow: 0 6px 18px rgba(68, 54, 66, 0.08);
  transition: transform .15s ease, box-shadow .15s ease;
}
.hs-card:hover { transform: translateY(-2px); box-shadow: 0 10px 24px rgba(68, 54, 66, 0.13); }
.hs-pink { background: #F8C8DC; } .hs-lavender { background: #E6D9F2; }
.hs-peach { background: #FFD6C2; } .hs-mint { background: #D8F3DC; }
.hs-white { background: #FFFFFF; } .hs-purple { background: #CDB4DB; }
.hs-card h4 { margin: 0 0 .4rem 0; font-family: 'Playfair Display', Georgia, serif; }
.hs-card p { margin: 0; }
.hs-quote { font-size: 1.25rem; font-style: italic; text-align: center; padding: 1.4rem; }
.hs-small { font-size: .9rem; opacity: .8; }

.hs-empty {
  text-align: center; background: rgba(255,255,255,.75); border: 2px dashed #CDB4DB;
  border-radius: 22px; padding: 1.8rem 1rem; margin: .8rem 0;
}
.hs-empty .big { font-size: 2.4rem; }

.hs-bubble-user, .hs-bubble-ai { padding: .8rem 1rem; border-radius: 18px; margin: .2rem 0; }
.hs-bubble-user { background: #F8C8DC; }
.hs-bubble-ai { background: #E6D9F2; }

.hs-daycell { text-align: center; border-radius: 16px; padding: .6rem .2rem; background: #FFFFFF; }
.hs-daycell .emoji { font-size: 1.6rem; }

/* ---------- buttons ---------- */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
  background: linear-gradient(135deg, #D96C9D, #B58AD1); color: #FFFFFF; border: none;
  border-radius: 999px; padding: .5rem 1.3rem; font-weight: 700;
  box-shadow: 0 4px 12px rgba(217, 108, 157, 0.35);
  transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-1px); box-shadow: 0 8px 18px rgba(217, 108, 157, 0.45); color: #FFFFFF;
}
.stButton > button:disabled { background: #CDB4DB; box-shadow: none; opacity: .7; }

/* ---------- inputs, tabs, expanders ---------- */
.stTextInput input, .stTextArea textarea, .stDateInput input, .stNumberInput input {
  background: #FFFFFF; border-radius: 14px; color: var(--plum);
}
.stTabs [data-baseweb="tab-list"] { gap: .4rem; }
.stTabs [data-baseweb="tab"] { border-radius: 999px; padding: .4rem 1rem; background: rgba(255,255,255,.6); }
.stTabs [aria-selected="true"] { background: #F8C8DC; font-weight: 700; }
[data-testid="stExpander"] {
  background: rgba(255,255,255,.85); border-radius: 18px; border: 1px solid #E6D9F2;
}
[data-testid="stProgress"] div[role="progressbar"] > div,
.stProgress > div > div > div > div { background: linear-gradient(90deg, #F8C8DC, #D96C9D); }

/* ---------- phones ---------- */
@media (max-width: 640px) {
  .hs-title { font-size: 2.1rem; }
  .hs-hero { padding: 1.4rem 1rem; }
  .block-container { padding-left: 1rem; padding-right: 1rem; }
}
</style>
"""


def apply_styles():
    """Add the custom CSS to the page."""
    st.markdown(CSS, unsafe_allow_html=True)
