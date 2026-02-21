# scoring.py — Lead scoring (max 100 pts)
# Bands: 70+ Hot, 45-69 Warm, 0-44 Cool
import re

def calc_score(lead: dict) -> int:
    s = 0
    if lead.get("type") == "School":           s += 20
    elif lead.get("type") == "Parent":         s += 10
    age = lead.get("child_age", "")
    if age in ("8–10 years", "11–13 years"):   s += 15
    elif age:                                  s += 8
    size = lead.get("school_size", "")
    if size == "1000+":                        s += 20
    elif size == "500–1000":                   s += 15
    elif size == "200–500":                    s += 10
    elif size == "Under 200":                  s += 5
    budget = lead.get("budget", "")
    if "3,000" in budget:                      s += 15
    elif "1,500" in budget:                    s += 12
    elif "500" in budget and "1,500" not in budget: s += 8
    elif "Under" in budget:                    s += 3
    goals = lead.get("goals", "")
    if any(k in goals for k in ("Coding", "Competitive")): s += 10
    elif goals:                                s += 5
    if lead.get("wants_demo"):                 s += 25
    else:                                      s += 5
    if re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", lead.get("email","")): s += 5
    if re.match(r"^[\d\s\+\-\(\)]{8,15}$",     lead.get("phone","")): s += 5
    return min(s, 100)

def score_label(score: int) -> dict:
    if score >= 70: return {"text": "🔥 Hot",  "cls": "hot"}
    if score >= 45: return {"text": "🟠 Warm", "cls": "warm"}
    return               {"text": "🔵 Cool", "cls": "cool"}
