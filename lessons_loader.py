import json

with open("lessons.json", "r", encoding="utf-8") as f:
    _raw = json.load(f)

LESSONS = {
    i
    + 1: {
        "topic": l["topic"],
        "summary": l["summary"],
        "keywords": l["keywords"],
        "practice": l.get("practice", ""),
    }
    for i, l in enumerate(_raw)
}
TOTAL_LESSONS = len(LESSONS)
