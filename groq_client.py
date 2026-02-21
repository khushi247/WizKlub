# groq_client.py
# Model: llama-3.3-70b-versatile (Groq, free tier)

import os
import requests
import streamlit as st
from wizklub_context import WIZKLUB_KNOWLEDGE

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_key() -> str:
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    key = st.session_state.get("groq_key", "")
    if key:
        return key
    return os.environ.get("GROQ_API_KEY", "")


def has_key() -> bool:
    return bool(get_key())


def _call(messages: list, max_tokens: int = 300, temperature: float = 0.7) -> str:
    key = get_key()
    if not key:
        return ""
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": messages,
                  "max_tokens": max_tokens, "temperature": temperature},
            timeout=20,
        )
        data = r.json()
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


# ── 1. Main Q&A — handles BOTH WizKlub questions AND irrelevant messages ──────
#
# The model does two things in one call:
#   a) Decides if the message is relevant to WizKlub/education
#   b) If yes, answers from the knowledge base
#      If no, returns the literal word IRRELEVANT so we show a polite deflection
#
# DEMO RULE: Only mention a demo if the person explicitly asked about
# next steps or signing up. Never volunteer it unprompted.

def answer_question(user_msg: str, lead: dict, history: list) -> str:
    name = lead.get("name", "")
    name_str = f", {name}" if name else ""

    system = f"""You are Wiz, a friendly assistant for WizKlub — a children's EdTech company in India.

First, decide if this message is RELEVANT or IRRELEVANT to WizKlub or education.

RELEVANT = anything about WizKlub, children's learning, programs, pricing, schedules,
how classes work, school partnerships, subjects taught, STEM, coding, critical thinking, etc.

IRRELEVANT = anything completely unrelated. Examples: "I'm hungry", "tell me a joke",
"what's the weather", "who won the match", random greetings with no question, gibberish.

If IRRELEVANT — respond with exactly this word and nothing else: IRRELEVANT

If RELEVANT — answer using ONLY the verified information below. Never invent facts.
If the question isn't covered below, say "our team can clarify that for you."

=== VERIFIED WIZKLUB INFORMATION ===
{WIZKLUB_KNOWLEDGE}
=== END ===

What you know about this visitor so far:
- Type: {lead.get('type') or 'not yet identified'}
- Child age: {lead.get('child_age') or 'not yet asked'}
- Goals: {lead.get('goals') or 'not yet asked'}
- School size: {lead.get('school_size') or 'not yet asked'}
- Name: {name or 'not yet given'}

STRICT RULES when answering:
1. Answer the question directly — 2 to 3 sentences max
2. Be warm and personalise using what you know about this visitor
3. ONLY mention booking a demo or next steps if the person explicitly asked about it
4. Do NOT add "book a demo" or "shall I set one up?" at the end of every reply
5. If they didn't ask about next steps, just answer the question and stop"""

    msgs = [{"role": "system", "content": system}]
    for h in history[-6:]:
        msgs.append({
            "role": "assistant" if h["role"] == "bot" else "user",
            "content": h["text"],
        })
    msgs.append({"role": "user", "content": user_msg})

    result = _call(msgs, max_tokens=250, temperature=0.7)

    # Empty result OR model returned IRRELEVANT → show polite deflection
    if not result or result.strip().upper() == "IRRELEVANT":
        return (
            f"Ha, that's a bit outside my expertise{name_str}! 😄 "
            "I'm here to help with anything about WizKlub — "
            "programs, how classes work, pricing, schedules, school partnerships. "
            "What would you like to know?"
        )

    return result


# ── 2. Qualification insight — one personalised sentence after goals/budget ───
# No demo mention here — this is just a warm acknowledgement of their situation.

def qualification_insight(lead: dict) -> str:
    if lead.get("type") == "Parent":
        prompt = (
            f"A parent has a child aged {lead.get('child_age')} wanting: {lead.get('goals')}. "
            f"WizKlub programs: HOTS (critical thinking/competitive prep ages 6-14), "
            f"SmartTech/YPDP (coding + robotics), WizBlock (beginner coding age 5+). "
            f"Write ONE warm sentence (under 25 words) recommending the best fit program. "
            f"Be specific. Start with an emoji. No quotes. Do NOT mention demos or booking."
        )
    else:
        prompt = (
            f"A school with {lead.get('school_size')} students has a STEM budget of {lead.get('budget')}. "
            f"WizKlub's school program integrates into curriculum for Grades 1-9 with teacher training. "
            f"Write ONE warm specific sentence (under 25 words) about what WizKlub can offer them. "
            f"Start with an emoji. No quotes. Do NOT mention demos or booking."
        )
    msgs = [
        {"role": "system", "content": "You are a helpful assistant for WizKlub EdTech. Be specific, warm, and brief."},
        {"role": "user", "content": prompt},
    ]
    return _call(msgs, max_tokens=70, temperature=0.8)


# ── 3. Closing message after CTA — warm, personal, no demo mention ────────────

def ai_closing(lead: dict) -> str:
    who = (
        f"parent of a {lead.get('child_age')} child interested in {lead.get('goals')}"
        if lead.get("type") == "Parent"
        else f"school representative for a {lead.get('school_size')} student school"
    )
    msgs = [
        {"role": "system", "content": "Write short warm personalised messages for WizKlub EdTech. Never mention demos."},
        {"role": "user", "content": (
            f"Write one warm enthusiastic sentence for {lead.get('name', 'them')}, "
            f"a {who}, expressing genuine excitement about their learning journey ahead. "
            f"Under 20 words. Start with an emoji. No quotes. No mention of demos."
        )},
    ]
    return _call(msgs, max_tokens=60, temperature=0.9)
