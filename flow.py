# flow.py — Conversation flow (rule-based + AI hybrid)

import re
import streamlit as st
from scoring import calc_score
from groq_client import answer_question, qualification_insight, ai_closing, has_key

def bot(t): st.session_state.messages.append({"role": "bot",  "text": t})
def user(t): st.session_state.messages.append({"role": "user", "text": t})
def opts(o): st.session_state.options = o
def step(s): st.session_state.step = s
def L(): return st.session_state.lead
def H(): return st.session_state.messages


def start_greeting():
    bot("👋 Hi! I'm Wiz, WizKlub's learning guide.")
    bot(
        "WizKlub builds critical thinking, coding & STEM skills in children aged 6–14 "
        "through research-backed programs trusted by 50,000+ families and 200+ schools. 🌱\n\n"
        "Who are you exploring this for?"
    )
    opts(["👨‍👩‍👧 My child — I'm a parent", "🏫 My school / institution"])
    step(1)


def route(text: str):
    s  = st.session_state.step
    aw = st.session_state.awaiting

    # Typed field collection — rule-based, no AI
    if aw == "name":  handle_name(text);  return
    if aw == "email": handle_email(text); return
    if aw == "phone": handle_phone(text); return

    # Mid-flow: any typed input that isn't clicking one of the shown buttons
    # gets sent to the AI. The AI itself decides if it's relevant or not —
    # we no longer do keyword matching here, that was too brittle.
    # s can be int or string ("ss"/"sb") so check type before numeric compare.
    mid_flow = (isinstance(s, int) and 1 < s < 7) or s in ("ss", "sb")
    if mid_flow and not _is_option_pick(text):
        user(text)
        opts([])
        if has_key():
            reply = answer_question(text, L(), H())
            bot(reply)
        else:
            bot("Let me finish getting your details first — then I can answer anything! 😊")
        _reshow(s)
        return

    handlers = {
        1: handle_type, 2: handle_child_age, 3: handle_goals,
        "ss": handle_school_size, "sb": handle_school_budget,
        4: handle_name, 5: handle_email, 6: handle_phone,
        7: handle_cta, 8: handle_freeform,
    }
    if s in handlers:
        handlers[s](text)


def handle_type(v):
    user(v)
    L()["type"] = "Parent" if "parent" in v.lower() or "child" in v.lower() else "School"
    if L()["type"] == "Parent":
        bot("Great! Let's find the right program for your child. How old are they?")
        opts(["5–7 years", "8–10 years", "11–13 years", "14–16 years"])
        step(2)
    else:
        bot(
            "Wonderful! WizKlub's school program integrates into your curriculum, "
            "includes teacher training, and runs for Grades 1–9. 🏫\n\n"
            "How many students are enrolled?"
        )
        opts(["Under 200", "200–500", "500–1000", "1000+"])
        step("ss")


def handle_child_age(v):
    user(v)
    L()["child_age"] = v
    bot("What's the most important outcome you're looking for?")
    opts([
        "💻 Coding & programming",
        "🧠 Critical thinking & reasoning",
        "🏆 Competitive exam prep",
        "🎮 Fun, creative STEM learning",
    ])
    step(3)


def handle_goals(v):
    user(v)
    L()["goals"] = v
    if has_key():
        insight = qualification_insight(L())
        if insight:
            bot(insight)
    bot(
        f"We have structured programs for the {L()['child_age']} range with measurable "
        "progress tracked every 4 weeks. To send you the right curriculum — what's your name?"
    )
    opts([])
    st.session_state.awaiting = "name"
    step(4)


def handle_school_size(v):
    user(v)
    L()["school_size"] = v
    bot("What's your approximate per-student STEM budget annually?")
    opts(["Under ₹500", "₹500–₹1,500", "₹1,500–₹3,000", "₹3,000+", "Not finalised yet"])
    step("sb")


def handle_school_budget(v):
    user(v)
    L()["budget"] = v
    if has_key():
        insight = qualification_insight(L())
        if insight:
            bot(insight)
    bot(
        f"Our partnerships team works with schools of {L()['school_size']} students regularly "
        "and can build a fully costed proposal. Who should we address it to?"
    )
    opts([])
    st.session_state.awaiting = "name"
    step(4)


def handle_name(v):
    user(v)
    L()["name"] = v.strip()
    bot(f"Nice to meet you, {L()['name']}! 😊 What's your email address?")
    st.session_state.awaiting = "email"
    step(5)


def handle_email(v):
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v.strip()):
        bot("That email doesn't look right — could you double check? (e.g. you@example.com)")
        return
    user(v)
    L()["email"] = v.strip()
    bot("And your phone number? Our team usually follows up within 2 hours.")
    st.session_state.awaiting = "phone"
    step(6)


def handle_phone(v):
    if not re.match(r"^[\d\s\+\-\(\)]{8,15}$", v.strip()):
        bot("Please enter a valid phone number (at least 8 digits).")
        return
    user(v)
    L()["phone"] = v.strip()
    st.session_state.awaiting = None
    bot(f"Almost done, {L()['name']}! How would you like to move forward?")
    opts([
        "📅 Book a free demo session",
        "📩 Send me details by email first",
        "🗣️ I'd like to speak to someone now",
    ])
    step(7)


def handle_cta(v):
    user(v)
    L()["wants_demo"] = "demo" in v.lower()
    if L()["wants_demo"]:
        st.session_state.demo_count += 1
    L()["score"] = calc_score(L())
    st.session_state.all_leads.append(dict(L()))

    # Confirmation — demo is mentioned here because the person explicitly chose it
    if "demo" in v.lower():
        bot(
            f"🚀 Confirmed, {L()['name']}! Our team will be in touch within 2 hours.\n\n"
            "You can also pick a slot directly: https://calendly.com/wizklub-demo"
        )
    elif "email" in v.lower():
        bot(f"📩 A full program overview will be in {L()['email']}'s inbox within the hour.")
    else:
        bot(f"📞 Someone from our team will call {L()['phone']} within 30 minutes during business hours.")

    # AI-generated warm closing — no demo mention (enforced in groq_client)
    if has_key():
        closing = ai_closing(L())
        if closing:
            bot(closing)

    # Open the floor for questions — no demo push
    bot("Feel free to ask me anything about WizKlub — programs, how classes work, fees, anything! 😊")
    step(8)


def handle_freeform(text):
    # Step 8: all messages go to AI.
    # The AI handles WizKlub questions AND irrelevant ones (deflects politely).
    # No fallback demo mention here.
    user(text)
    if has_key():
        bot(answer_question(text, L(), H()))
    else:
        bot(
            "Happy to help — reach us at hello@wizklub.com and the team will answer anything! 😊"
        )


def _is_option_pick(text: str) -> bool:
    return any(text.strip() == o.strip() for o in st.session_state.get("options", []))


def _reshow(s):
    m = {
        1:    ["👨‍👩‍👧 My child — I'm a parent", "🏫 My school / institution"],
        2:    ["5–7 years", "8–10 years", "11–13 years", "14–16 years"],
        3:    ["💻 Coding & programming", "🧠 Critical thinking & reasoning",
               "🏆 Competitive exam prep", "🎮 Fun, creative STEM learning"],
        "ss": ["Under 200", "200–500", "500–1000", "1000+"],
        "sb": ["Under ₹500", "₹500–₹1,500", "₹1,500–₹3,000", "₹3,000+", "Not finalised yet"],
        7:    ["📅 Book a free demo session", "📩 Send me details by email first",
               "🗣️ I'd like to speak to someone now"],
    }
    if s in m:
        opts(m[s])
