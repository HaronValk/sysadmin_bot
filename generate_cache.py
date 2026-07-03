#!/usr/bin/env python3
import json, sqlite3, time
from openai import OpenAI

import os
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DB_PATH = "cache.db"
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

with open("lessons.json", "r", encoding="utf-8") as f:
    lessons = json.load(f)

SYSTEM_PROMPT = (
    "Ты — легендарный системный администратор и девопс-инженер с 20-летним стажем. "
    "Твой стиль — уверенный, с лёгкой иронией и байками из жизни. "
    "Объясняешь сложные вещи простым языком, с примерами и командами. "
    "Не используешь Markdown-разметку. Код пиши с новой строки."
)


def get_completed_ids():
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT lesson_id FROM lessons_cache").fetchall()
        conn.close()
        return {row[0] for row in rows}
    except:
        return set()


completed = get_completed_ids()
print(f"Уже сгенерировано: {len(completed)} уроков")

for idx, lesson in enumerate(lessons, start=1):
    if idx in completed:
        print(f"[{idx}/{len(lessons)}] {lesson['topic']} — уже готов")
        continue

    topic = lesson["topic"]
    print(f"\n[{idx}/{len(lessons)}] {topic} (НОВЫЙ)")

    full_text = ""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Тема: {topic}\n{lesson['summary']}\nКлючевые слова: {', '.join(lesson['keywords'])}\n\nРасскажи подробно этот материал с примерами и командами.",
        },
    ]

    for attempt in range(10):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
            )
            part = resp.choices[0].message.content
            finish = resp.choices[0].finish_reason
            full_text += part
            print(f"  Часть {attempt+1}: {len(part)} символов (finish: {finish})")
            if finish == "stop":
                break
            messages.append({"role": "assistant", "content": part})
            messages.append(
                {
                    "role": "user",
                    "content": "Продолжи ровно с того места, где остановился.",
                }
            )
            time.sleep(2)
        except Exception as e:
            if "402" in str(e):
                print("💰 Недостаточно средств. Пополни баланс и нажми Enter...")
                input()
                continue
            print(f"❌ Ошибка: {e}")
            time.sleep(10)
            if attempt == 9:
                full_text = f"ОШИБКА ГЕНЕРАЦИИ: {e}"
            continue
    if full_text and not full_text.startswith("ОШИБКА"):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO lessons_cache VALUES (?,?)", (idx, full_text)
            )
        completed.add(idx)
        print(f"  ✅ Сохранено: {len(full_text)} символов")
    else:
        print(f"  ⚠️ Пропущено")
    time.sleep(1)

print(f"\nГотово! Уроков в кэше: {len(completed)}")
