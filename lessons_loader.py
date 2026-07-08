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
        "project_step_ru": l.get("project_step_ru", ""),
        "project_step_global": l.get("project_step_global", ""),
    }
    for i, l in enumerate(_raw)
}
TOTAL_LESSONS = len(LESSONS)
