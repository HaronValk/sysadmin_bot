# format_project_steps.py
import json, time, os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

with open("lessons.json", "r", encoding="utf-8") as f:
    lessons = json.load(f)

FORMAT_PROMPT = """Ты — эксперт по форматированию. ОБЯЗАТЕЛЬНО оберни ВСЕ команды (даже однострочные) в ``` с указанием языка.

ПРАВИЛА (нарушать нельзя):
1. Любая строка, которая является командой (начинается с Get-, Set-, New-, net, ipconfig, ping, slmgr, docker, kubectl, git, npm, pip, python, bash, powershell, Initialize-, New-ItemProperty, net localgroup, net user, systemctl, apt, yum, sudo, и т.д.) — ОБЯЗАТЕЛЬНО оберни в ```powershell или ```bash
2. Заголовки начинай с ##
3. Списки через -
4. Термины выделяй **жирным**
5. Сохрани ВЕСЬ исходный текст
6. НЕ пропускай ни одной команды — даже однострочные должны быть в ```

Пример:
## Заголовок
Выполни команду:

```powershell
net localgroup IT-Admins
```"""

for i, lesson in enumerate(lessons, start=1):
    ru_step = lesson.get("project_step_ru", "")
    if ru_step and len(ru_step) > 50:
        print(f"[{i}/{len(lessons)}] Форматирую РФ-шаг: {lesson.get('topic', '')}")
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": FORMAT_PROMPT},
                    {"role": "user", "content": ru_step},
                ],
                temperature=0.3,
                max_tokens=1200,
            )
            lesson["project_step_ru"] = resp.choices[0].message.content.strip()
            print(f"  ✅ Готово")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
        time.sleep(0.5)

    global_step = lesson.get("project_step_global", "")
    if global_step and len(global_step) > 50:
        print(f"[{i}/{len(lessons)}] Форматирую Global-шаг: {lesson.get('topic', '')}")
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": FORMAT_PROMPT},
                    {"role": "user", "content": global_step},
                ],
                temperature=0.3,
                max_tokens=1200,
            )
            lesson["project_step_global"] = resp.choices[0].message.content.strip()
            print(f"  ✅ Готово")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
        time.sleep(0.5)

with open("lessons.json", "w", encoding="utf-8") as f:
    json.dump(lessons, f, ensure_ascii=False, indent=2)

print("\nГотово! Все шаги отформатированы.")
