from openai import OpenAI
from config import DEEPSEEK_API_KEY

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
SYSTEM_PROMPT = "Ты — опытный сисадмин и девопс. Объясняешь понятно, с примерами и командами. Без Markdown."

def ask_ai(question, lesson_id=None):
    from lessons_loader import LESSONS
    ctx = f"Тема: {LESSONS[lesson_id]['topic']}" if lesson_id else "Общий вопрос"
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role":"system","content":SYSTEM_PROMPT}, {"role":"user","content":f"{ctx}\n\n{question}"}],
            temperature=0.7, max_tokens=1000
        )
        return resp.choices[0].message.content, resp.usage
    except Exception as e:
        return f"⚠️ Ошибка: {e}", None