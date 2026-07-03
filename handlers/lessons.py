from telegram import Update
from telegram.ext import ContextTypes
from db import get_cached_lesson, load_progress, save_progress
from lessons_loader import LESSONS, TOTAL_LESSONS
from utils import split_content, strip_html
from keyboards import lesson_keyboard


async def show_lesson(update_or_query, lid, uid, part=1):
    content = get_cached_lesson(lid)
    if not content:
        text = "⚠️ Урок ещё не сгенерирован."
        total_parts = 1
    else:
        lesson = LESSONS[lid]
        header = f"📘 Урок {lid}/{TOTAL_LESSONS}\n📌 {lesson['topic']}\n\n🔎 {lesson['summary']}\n────────────────────\n\n"
        parts = split_content(strip_html(content))
        total_parts = len(parts)
        text = header + parts[min(part - 1, total_parts - 1)]
    kb = lesson_keyboard(lid, uid, part, total_parts if content else 1)
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text=text, reply_markup=kb)
    else:
        await update_or_query.reply_text(text=text, reply_markup=kb)


async def next_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    last = load_progress(uid)
    nxt = last + 1
    if nxt > TOTAL_LESSONS:
        await update.message.reply_text("🎉 Всё пройдено!")
        return
    save_progress(uid, nxt)
    await show_lesson(update.message, nxt, uid)


async def show_practice(query, lid):
    from lessons_loader import LESSONS

    lesson = LESSONS[lid]
    practice_text = lesson.get("practice", "Задание отсутствует.")
    await query.message.reply_text(
        f"📝 Задание к уроку {lid}: {lesson['topic']}\n\n{practice_text}"
    )
