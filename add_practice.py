# add_practice.py
import json, time
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

with open("lessons.json", "r", encoding="utf-8") as f:
    lessons = json.load(f)

for i, lesson in enumerate(lessons, start=1):
    if "practice" in lesson:
        print(f"[{i}/{len(lessons)}] {lesson['topic']} — уже есть задание")
        continue

    print(f"[{i}/{len(lessons)}] {lesson['topic']} — генерирую...")

    prompt = f"""Ты — опытный системный администратор. Придумай ОДНО практическое задание для урока на тему:
"{lesson['topic']}"
Описание урока: {lesson['summary']}

Требования к заданию:
- Конкретное, выполнимое за 15-30 минут
- Связано с реальной работой сисадмина
- Максимум 2-3 предложения
- На русском языке
- Без маркдауна, просто текст"""

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        practice = resp.choices[0].message.content.strip()
        lesson["practice"] = practice
        print(f"  ✅ {practice[:80]}...")
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        lesson["practice"] = "Выполни лабораторную работу по теме урока."

    time.sleep(0.5)  # чтобы не упереться в rate limit

with open("lessons.json", "w", encoding="utf-8") as f:
    json.dump(lessons, f, ensure_ascii=False, indent=2)

print(f"\nГотово! Добавлены задания для всех уроков.")
