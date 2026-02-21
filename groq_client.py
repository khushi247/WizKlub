# groq_client.py
# Model: llama-3.3-70b-versatile (Groq, free tier)
# Key reading: checks secrets first, then session state, then env var
# Never silently fails without telling us why

import os
import requests
import streamlit as st
from wizklub_context import WIZKLUB_KNOWLEDGE

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_key() -> str:
    """
    Try to get the Groq API key from multiple sources in order:
    1. Streamlit secrets (production on Streamlit Cloud)
    2. st.session_state (user pasted it in)
    3. Environment variable (local .env usage)
    Returns empty string if none found.
    """
    # Try Streamlit secrets
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # Try session state
    key = st.session_state.get("groq_key", "")
    if key:
        return key

    # Try environment variable
    key = os.environ.get("GROQ_API_KEY", "")
    return key


def has_key() -> bool:
    return bool(get_key())


def _call(messages: list, max_tokens: int = 300, temperature: float = 0.7) -> str:
    """
    Make a Groq API call.
    Returns the text response, or empty string on failure.
    Prints the actual error so we can debug — no more silent failures.
    """
    key = get_key()
    if not key:
        return ""

    try:
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model":       GROQ_MODEL,
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": temperature,
            },
            timeout=20,
        )
        data = r.json()

        # Surface API errors properly instead of hiding them
        if "error" in data:
            print(f"[Groq Error] {data['error']}")
            return ""

        return data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        print("[Groq] Request timed out")
        return ""
    except Exception as e:
        print(f"[Groq] Exception: {e}")
        return ""


# ── 1. Main Q&A — answers ANY question using real WizKlub knowledge ───────────
def answer_question(user_msg: str, lead: dict, history: list) -> str:
    system = f"""You are Wiz, a friendly and knowledgeable assistant for WizKlub.

Use the verified WizKlub information below to answer questions accurately.
If a question is not covered in the info, say "our team will cover that in the demo" — never make up facts.

=== WIZKLUB VERIFIED INFORMATION ===
{WIZKLUB_KNOWLEDGE}
=== END ===

About this visitor:
- Type: {lead.get('type') or 'not yet identified'}
- Child age: {lead.get('child_age') or 'not yet asked'}
- Goals: {lead.get('goals') or 'not yet asked'}
- School size: {lead.get('school_size') or 'not yet asked'}
- Name: {lead.get('name') or 'not yet given'}

Answer rules:
1. Answer the actual question directly using the info above
2. Keep it warm and concise — 2 to 3 sentences max
3. Personalise based on what you know about them
4. End with a gentle nudge toward booking a demo"""

    msgs = [{"role": "system", "content": system}]
    for h in history[-6:]:
        msgs.append({
            "role": "assistant" if h["role"] == "bot" else "user",
            "content": h["text"],
        })
    msgs.append({"role": "user", "content": user_msg})

    result = _call(msgs, max_tokens=250, temperature=0.7)
    if not result:
        name = lead.get("name", "")
        return (
            f"Great question{', ' + name if name else ''}! "
            "Our team will walk you through this in detail during the free demo — "
            "shall I set one up for you? 😊"
        )
    return result


# ── 2. Personalised insight after goals/budget collected ─────────────────────
def qualification_insight(lead: dict) -> str:
    if lead.get("type") == "Parent":
        prompt = (
            f"A parent has a child aged {lead.get('child_age')} wanting to focus on: {lead.get('goals')}. "
            f"WizKlub programs: HOTS (critical thinking/reasoning/competitive prep for ages 6-14), "
            f"SmartTech/YPDP (coding+robotics, builds real products), WizBlock (beginner coding age 5+). "
            f"Write ONE warm sentence (under 25 words) recommending the most relevant program. "
            f"Be specific. Start with emoji. No quotes."
        )
    else:
        prompt = (
            f"A school with {lead.get('school_size')} students has a STEM budget of {lead.get('budget')}. "
            f"WizKlub's school program integrates into the curriculum for Grades 1-9, "
            f"includes teacher training, hands-on projects, and custom proposals. "
            f"Write ONE warm sentence (under 25 words) about what WizKlub can offer. "
            f"Be specific. Start with emoji. No quotes."
        )

    msgs = [
        {"role": "system", "content": "You are a helpful assistant for WizKlub EdTech. Be specific, warm, and brief."},
        {"role": "user", "content": prompt},
    ]
    return _call(msgs, max_tokens=70, temperature=0.8)


# ── 3. Personalised closing after CTA ────────────────────────────────────────
def ai_closing(lead: dict) -> str:
    who = (
        f"parent of a {lead.get('child_age')} child interested in {lead.get('goals')}"
        if lead.get("type") == "Parent"
        else f"school rep for a {lead.get('school_size')} student school"
    )
    msgs = [
        {"role": "system", "content": "Write short warm personalised closing messages for WizKlub EdTech."},
        {"role": "user", "content": (
            f"Write one enthusiastic sentence for {lead.get('name', 'them')}, "
            f"a {who}. Under 20 words. Start with an emoji. No quotes."
        )},
    ]
    return _call(msgs, max_tokens=60, temperature=0.9)
