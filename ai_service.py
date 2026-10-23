"""
ai_service.py - everything that talks to Google Gemini.

Rules this file follows:
* The API key is read from an environment variable or Streamlit secrets.
  It is never written in the code and never shown in error messages.
* Nothing is sent to Gemini unless a function here is called, and the app
  only calls them when the user clicks an AI button.
* Every failure becomes an AIError with a friendly message.
"""

import json
import os
import re

# Official Google Gen AI SDK (package name: google-genai).
# Model ids change over time, so you can override this with the GEMINI_MODEL
# environment variable or secret without touching the code.
DEFAULT_MODEL = "gemini-3.6-flash"

MAX_TEXT_CHARS = 6000   # longest piece of user text we send in one request
MAX_CHAT_MESSAGES = 20  # how much recent chat history we send

NO_KEY_MESSAGE = (
    "Gemini is not set up yet, so AI features are switched off. "
    "Everything else in HerSpace AI still works! "
    "See the Settings page or the README to add your GEMINI_API_KEY."
)

SYSTEM_INSTRUCTION = (
    "You are AI Bestie, a warm, friendly helper inside a personal planner app called HerSpace AI. "
    "Be supportive, respectful, practical and concise. Use plain language and a few gentle emojis. "
    "You are an AI, not a human, therapist, doctor or any other professional: never claim to be one, "
    "never diagnose, and never give medical or mental-health treatment advice. "
    "Do not encourage the user to depend on you; encourage real-life friends, family and professionals "
    "when that would help. Avoid unrealistic beauty standards and body-shaming. "
    "If the user mentions self-harm, suicide or being in danger, respond with care, say you are an AI, "
    "and encourage them to contact local emergency services or a crisis line, or a trusted person nearby. "
    "You only know what the user has typed in this request."
)

LOCAL_AFFIRMATIONS = [
    "I am allowed to take things one small step at a time.",
    "My effort matters, even on the days it feels quiet.",
    "I can be proud of how far I have come and still be growing.",
    "I deserve rest, and resting does not make me lazy.",
    "I am learning, and learning takes patience.",
    "I can handle today by focusing on the next kind thing I can do.",
    "My feelings are valid, and they do not have to be perfect to be welcome.",
    "I choose progress over perfection.",
    "I can ask for help when I need it, and that is a strength.",
    "I am building a life that feels like mine.",
    "Small habits are shaping a bigger, brighter me.",
    "I can set gentle boundaries and still be kind.",
    "Mistakes are how I learn. They do not define me.",
    "I bring my own light to every room I walk into.",
    "I am worthy of care, from others and from myself.",
    "Today I will celebrate one tiny win.",
    "I can start again whenever I need to.",
    "My dreams are worth planning for, one step at a time.",
    "I am capable of learning difficult things.",
    "I allow myself to enjoy the little moments.",
    "I trust myself to figure things out, one step at a time.",
    "My pace is my pace, and that is okay.",
    "I am more than my to-do list.",
    "I can be soft and strong at the same time.",
    "I am grateful for the small good things in this day.",
]

LOCAL_JOURNAL_PROMPTS = [
    "What is one small thing that made today a little better?",
    "What are three things I am grateful for right now?",
    "What is weighing on my mind, and what is one small step I can take?",
    "Describe a moment this week when I felt proud of myself.",
    "What do I need more of in my life right now? What do I need less of?",
    "Write a kind note to myself about something I am working through.",
    "What would my ideal calm day look like?",
    "What did I learn recently that I want to remember?",
    "Who made me smile this week, and why?",
    "What is one thing I want to let go of?",
]


class AIError(Exception):
    """An error whose message is safe and friendly to show to the user."""


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

def _read_setting(name):
    """Look in environment variables first, then in Streamlit secrets."""
    value = os.environ.get(name)
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(name)
        except Exception:  # no secrets file, or Streamlit not installed
            value = None
    return (str(value).strip() if value else "")


def get_api_key():
    """Return the key, or None when it is missing or still a placeholder."""
    key = _read_setting("GEMINI_API_KEY") or _read_setting("GOOGLE_API_KEY")
    if not key or key.upper().startswith("YOUR_") or "PLACEHOLDER" in key.upper():
        return None
    return key


def is_configured():
    return get_api_key() is not None


def get_model_name():
    return _read_setting("GEMINI_MODEL") or DEFAULT_MODEL


# --------------------------------------------------------------------------
# Low-level calls
# --------------------------------------------------------------------------

def _call_model(contents, system_instruction, json_mode=False):
    """The only place that imports and calls the Google SDK."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise AIError("The Google Gen AI library is not installed. Run: pip install -r requirements.txt")

    client = genai.Client(api_key=get_api_key())
    config_args = {"system_instruction": system_instruction}
    if json_mode:
        config_args["response_mime_type"] = "application/json"

    if isinstance(contents, list):  # a chat history
        contents = [
            types.Content(role=item["role"], parts=[types.Part(text=item["text"])])
            for item in contents
        ]

    response = client.models.generate_content(
        model=get_model_name(),
        contents=contents,
        config=types.GenerateContentConfig(**config_args),
    )
    return response.text or ""


def _friendly_error(exc):
    """Turn any exception into a safe message. The raw error text is never shown."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    name = type(exc).__name__.lower()
    text = str(exc).lower()

    if code in (401, 403) or "permission" in name or "api key" in text or "api_key" in text:
        return "Gemini did not accept the API key. Please check that your GEMINI_API_KEY is correct and active."
    if code == 429 or "resource_exhausted" in text or "quota" in text:
        return "Gemini is getting too many requests right now (rate limit). Please wait a minute and try again."
    if code == 404:
        return "The Gemini model name was not found. Check the GEMINI_MODEL setting or update the app."
    if code == 400:
        return "Gemini could not process that request. Try shorter or simpler text."
    if isinstance(code, int) and code >= 500:
        return "Gemini is having a temporary problem. Please try again in a moment."
    if isinstance(exc, (ConnectionError, TimeoutError)) or "connect" in name or "timeout" in name:
        return "I could not reach Gemini. Please check your internet connection and try again."
    return "Something went wrong while contacting Gemini. Please try again."


def generate_text(contents, system_instruction=SYSTEM_INSTRUCTION, json_mode=False):
    """Send one request to Gemini and return the reply text (or raise AIError)."""
    if not is_configured():
        raise AIError(NO_KEY_MESSAGE)
    try:
        text = (_call_model(contents, system_instruction, json_mode) or "").strip()
    except AIError:
        raise
    except Exception as exc:
        raise AIError(_friendly_error(exc)) from None
    if not text:
        raise AIError("Gemini sent back an empty answer. Please try again.")
    return text


def _clip(text):
    return (text or "").strip()[:MAX_TEXT_CHARS]


# --------------------------------------------------------------------------
# Feature functions (one per AI button in the app)
# --------------------------------------------------------------------------

def chat_reply(history, user_message):
    """`history` is a list of {"role": "user" | "assistant", "content": "..."}."""
    messages = []
    for item in history[-MAX_CHAT_MESSAGES:]:
        role = "model" if item["role"] == "assistant" else "user"
        messages.append({"role": role, "text": _clip(item["content"])})
    messages.append({"role": "user", "text": _clip(user_message)})
    return generate_text(messages)


def journaling_prompts(topic=""):
    topic_line = f" The user would like prompts about: {_clip(topic)[:300]}." if topic.strip() else ""
    return generate_text(
        "Write 5 gentle, creative journaling prompts as a numbered list. "
        "Keep each prompt to one sentence." + topic_line
    )


def reflect_on_entry(title, content, mood=""):
    return generate_text(
        "The user chose to share this journal entry with you. Write a short, kind reflection "
        "(about 120 words): notice themes, validate feelings without diagnosing, and offer one or two "
        "gentle questions to think about.\n\n"
        f"Title: {_clip(title)[:200]}\nMood: {mood}\nEntry:\n{_clip(content)}"
    )


def summarize_entry(title, content):
    return generate_text(
        "Summarize this journal entry in 2 to 3 short sentences, in second person "
        "('You wrote about...').\n\n"
        f"Title: {_clip(title)[:200]}\nEntry:\n{_clip(content)}"
    )


def selfcare_suggestions(focus=""):
    focus_line = f" Focus area: {_clip(focus)[:300]}." if focus.strip() else ""
    return generate_text(
        "Suggest 6 simple, realistic self-care ideas that take 5 to 30 minutes each, as a short bullet "
        "list with a one-line reason each. Avoid beauty-standard pressure, expensive products and "
        "medical advice." + focus_line
    )


def new_affirmation():
    text = generate_text(
        "Write ONE short affirmation (1 to 2 sentences). It must be encouraging, realistic, inclusive "
        "and free of medical claims. Reply with only the affirmation text."
    )
    return text.strip().strip('"').strip("“”")


GOAL_PLAN_KEYS = ["summary", "steps", "timeline", "weekly_milestones", "checklist", "encouragement"]


def _extract_json(text):
    """Parse JSON even when the model wraps it in ```json fences."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass
    raise AIError("I could not read the plan Gemini sent back. Please try generating it again.")


def normalize_plan(data):
    """Make sure the plan always has every key, with the right types."""
    if not isinstance(data, dict):
        raise AIError("I could not read the plan Gemini sent back. Please try generating it again.")
    plan = {}
    for key in GOAL_PLAN_KEYS:
        value = data.get(key, [] if key in ("steps", "weekly_milestones", "checklist") else "")
        if key in ("steps", "weekly_milestones", "checklist"):
            if isinstance(value, str):
                value = [value]
            value = [str(v).strip() for v in value if str(v).strip()] if isinstance(value, list) else []
        else:
            value = str(value).strip()
        plan[key] = value
    if not plan["summary"] and not plan["steps"]:
        raise AIError("Gemini's plan was empty. Please try generating it again.")
    return plan


def goal_plan(title, description, progress, available_time, target_date, preferences):
    prompt = (
        "Create a realistic, encouraging plan for this personal goal. Reply ONLY with JSON using exactly "
        'these keys: "summary" (string), "steps" (list of strings), "timeline" (string), '
        '"weekly_milestones" (list of strings like "Week 1: ..."), "checklist" (list of 5 to 8 short '
        'strings), "encouragement" (string).\n\n'
        f"Goal: {_clip(title)[:200]}\n"
        f"Description: {_clip(description)[:1500]}\n"
        f"Current progress: {progress}%\n"
        f"Time available: {_clip(available_time)[:200] or 'not specified'}\n"
        f"Target date: {target_date or 'not set'}\n"
        f"Preferences: {_clip(preferences)[:1000] or 'none'}"
    )
    return normalize_plan(_extract_json(generate_text(prompt, json_mode=True)))
