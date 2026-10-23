# 🌸 HerSpace AI

> Your little corner to grow, glow, and become your best self.

HerSpace AI is a pastel, Pinterest-inspired personal companion app. It combines a digital diary, mood tracker,
self-care planner, goal planner, habit tracker, daily affirmations and a friendly AI chat helper.
It is built with Python and Streamlit, saves data in SQLite, and uses Google Gemini Flash for the AI features.

## ✨ Features

- 🏠 **Home**: date, daily affirmation, today's tasks, mood check-in, active goals, habit summary, recent activity
- 📔 **My Journal**: write, search, edit and delete entries (delete asks for confirmation); optional AI prompts, reflection and summary
- 🌸 **Mood Tracker**: 8 moods, notes, date filter, weekly summary, Plotly chart, edit and delete
- 🧴 **Self-Care Planner**: routines by category and schedule, daily checklist, history, optional AI ideas
- 🎯 **My Goals**: progress bars, AI plan (summary, steps, timeline, weekly milestones, checklist), edit and delete
- ✨ **Habit Tracker**: daily check-ins, real streaks and stats, Plotly charts, history, edit and delete
- 💖 **Daily Affirmations**: local collection, optional Gemini affirmations, saved favorites
- 🤖 **AI Bestie**: chat with message bubbles; only sees what you type in the chat
- ⚙️ **Settings**: app info, clear chat, export data (JSON), delete all data (with confirmation)

The app works **without** a Gemini key. Only the AI buttons are switched off, and they show a friendly message.

## 🖼️ Screenshots

Add your screenshots later:

1. Run the app and take screenshots of the pages you like.
2. Create a folder called `screenshots` and save the images there.
3. Add them to this README, for example:

```markdown
![Home page](screenshots/home.png)
```

## 🧰 Technology stack

- Python 3.10 or newer
- Streamlit (user interface and navigation)
- Google Gen AI SDK (`google-genai`) with a Gemini Flash model (default: `gemini-3.6-flash`)
- SQLite (built into Python)
- Pandas and Plotly

## 📁 Project structure

```text
herspace-ai/
├── app.py                 # Starts the app, sidebar navigation
├── views.py               # The content of every page
├── database.py            # SQLite tables and all database functions
├── ai_service.py          # All Gemini code, error handling, local affirmations
├── styles.py              # Colors and custom CSS
├── requirements.txt       # Python packages
├── tests/                 # Automated tests
├── .streamlit/
│   ├── config.toml            # Theme colors
│   └── secrets.toml.example   # Example secrets file (placeholder only)
├── .env.example           # Example environment file (placeholder only)
├── .gitignore             # Keeps secrets and private data out of GitHub
└── README.md
```

## ✅ Prerequisites

- Python 3.10 or newer ([python.org/downloads](https://www.python.org/downloads/))
- A free Gemini API key (optional, only for AI features): <https://aistudio.google.com/apikey>
- A GitHub account (for deployment)

## 💻 Installation

Open a terminal in the project folder.

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (Command Prompt):
venv\Scripts\activate.bat
# Mac / Linux:
source venv/bin/activate

# 3. Install the packages
pip install -r requirements.txt
```

If `python` does not work on Mac or Linux, try `python3`.

## ▶️ Run the app locally

```bash
streamlit run app.py
```

Your browser opens at <http://localhost:8501>.

## 🔑 Configure the Gemini API key locally

Choose **one** of these options.

**Option A: Streamlit secrets file (recommended)**

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
2. Open it and replace the placeholder with your real key:

```toml
GEMINI_API_KEY = "paste-your-real-key-here"
```

**Option B: environment variable**

```bash
# Mac / Linux
export GEMINI_API_KEY="paste-your-real-key-here"
# Windows PowerShell
$env:GEMINI_API_KEY="paste-your-real-key-here"
```

Then restart the app. `secrets.toml` and `.env` are listed in `.gitignore`, so Git will not upload them.

To use a different Gemini model, add `GEMINI_MODEL = "model-name"` to your secrets or set the `GEMINI_MODEL` environment variable.

## 🚀 Deploy on Streamlit Community Cloud

1. Push the project to GitHub (see below).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **Create app** and choose to deploy from an existing GitHub repository.
4. Choose your repository and branch (`main`), and set the main file path to `app.py`.
5. Open **Advanced settings** and paste this into **Secrets**:

```toml
GEMINI_API_KEY = "paste-your-real-key-here"
```

6. Click **Deploy** and wait for the build to finish.

Streamlit's menus can change, so if a button has moved, check the
[official deployment docs](https://docs.streamlit.io/deploy/streamlit-community-cloud).

## 🐙 Push the project to GitHub

1. Create a new **empty** repository on <https://github.com/new> (for example `herspace-ai`). Do not tick "Add a README".
2. In your project folder run:

```bash
git init
git add .
git status
```

3. Check the `git status` list. You must **not** see `secrets.toml`, `.env`, `data/` or any `.db` file. If you do, stop and check `.gitignore`.
4. Then run:

```bash
git commit -m "Add HerSpace AI"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/herspace-ai.git
git push -u origin main
```

If you prefer the browser, you can also drag and drop files on the GitHub "uploading an existing file" page. Do not upload `.env`, `secrets.toml` or the `data` folder.

## 🧪 Run the tests

```bash
python -m unittest discover -s tests -v
```

The tests need no internet and no API key. They cover the database (journal, moods, routines, goals, habits, favorites, export, delete) and the Gemini error handling.

## 🔒 Privacy and security notes

- Journal entries are sent to Gemini **only** when you click an AI button on that entry.
- AI Bestie only sees what you type in the chat. It does not read your journal, moods, goals or habits.
- The app does not write your private text to logs.
- The API key is read from Streamlit secrets or an environment variable. It is never stored in SQLite or in the code.
- This version has **no login and no user accounts**. It is meant for one person using their own copy. A public deployment would show the same data to everyone who opens it.
- AI replies are general suggestions. The app is not a therapist, doctor or medical tool, and mood records are not a mental health assessment.

## ⚠️ Known limitations

- **SQLite on Streamlit Community Cloud is not permanent storage.** The app's files can be reset when it restarts or is redeployed, so saved entries may disappear. Use **Settings > Export** to back up your data. For a public multi-user version, use a hosted database such as Supabase (PostgreSQL), Neon or Firebase, and add real authentication.
- Dates use the server's clock and time zone (often UTC on cloud hosting).
- No theme switching: there is one pastel theme.
- AI chat history lives only in the current browser session.
- The first version was checked with automated tests and a simulated run of every page. It was **not** opened in a real browser or deployed by the author, so please test the pages yourself after installing.

## 🌈 Future improvements

- User accounts and a hosted database
- Optional PIN lock
- Import data from a JSON export
- Light and dark theme switch
- Reminders and a weekly review page
