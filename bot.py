#!/usr/bin/env python3
import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import TELEGRAM_TOKEN
from db import (
    init_db,
    load_progress,
    save_progress,
    add_favorite,
    remove_favorite,
    get_favorite_ids,
)
from lessons_loader import TOTAL_LESSONS
from keyboards import list_keyboard, lesson_keyboard
from utils import strip_html, split_content
from handlers.start import start
from handlers.lessons import show_lesson, next_lesson, show_practice
from handlers.plan import plan, favorites, completed as show_completed
from handlers.notes import note_command
from handlers.tokens import tokens
from handlers.ask import ask
from mini_app import start as start_miniapp
from lessons_loader import LESSONS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def handle_callback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = update.effective_user.id

    if data.startswith("prev_"):
        await show_lesson(q, int(data[5:]), uid)
    elif data.startswith("next_"):
        await show_lesson(q, int(data[5:]), uid)
    elif data.startswith("part_"):
        _, lid, part = data.split("_")
        lid, part = int(lid), int(part)
        from db import get_cached_lesson

        content = get_cached_lesson(lid)
        lesson = LESSONS[lid]
        header = f"📘 Урок {lid}/{TOTAL_LESSONS}\n📌 {lesson['topic']}\n\n🔎 {lesson['summary']}\n────────────────────\n\n"
        parts = split_content(strip_html(content))
        total_parts = len(parts)
        text = header + parts[min(part - 1, total_parts - 1)]
        kb = lesson_keyboard(lid, uid, part, total_parts)
        try:
            await q.edit_message_text(text=text, reply_markup=kb)
        except Exception as e:
            logger.warning(f"Part edit error: {e}")
    elif data.startswith("open_"):
        await show_lesson(q, int(data[5:]), uid)
    elif data.startswith("fav_") or data.startswith("unfav_"):
        lid = int(data.split("_", 1)[1])
        if data.startswith("fav_"):
            add_favorite(uid, lid)
        else:
            remove_favorite(uid, lid)
        await q.answer("Готово!")
        try:
            await q.edit_message_reply_markup(reply_markup=lesson_keyboard(lid, uid))
        except Exception as e:
            logger.warning(f"Fav keyboard error: {e}")
    elif data.startswith("note_"):
        lid = int(data.split("_")[1])
        await q.message.reply_text(
            f"📒 Заметки к уроку {lid}:\n/note добавить <текст>\n/note список\n/note удалить <id>"
        )
    elif "_page_" in data or data.startswith("plan_") or data.startswith("completed_"):
        prefix, page_str = data.rsplit("_", 1)
        page = int(page_str)
        if "plan" in prefix:
            items = list(range(1, TOTAL_LESSONS + 1))
        elif "fav" in prefix:
            items = get_favorite_ids(uid)
        elif "completed" in prefix:
            items = list(range(1, load_progress(uid) + 1))
        else:
            return
        try:
            await q.edit_message_reply_markup(
                reply_markup=list_keyboard(items, page, nav_prefix=prefix)
            )
        except Exception as e:
            logger.warning(f"Pagination error: {e}")
    elif data.startswith("plan") and data[4:].isdigit():
        page = int(data[4:])
        items = list(range(1, TOTAL_LESSONS + 1))
        try:
            await q.edit_message_reply_markup(
                reply_markup=list_keyboard(items, page, nav_prefix="plan_")
            )
        except Exception as e:
            logger.warning(f"Legacy pagination error: {e}")
    elif data.startswith("practice_"):
        lid = int(data.split("_")[1])
        from handlers.lessons import show_practice

        await show_practice(q, lid)


async def handle_message(update, context):
    text = update.message.text
    uid = update.effective_user.id
    if text == "▶️ Начать обучение":
        await next_lesson(update, context)
    elif text == "📊 Прогресс":
        comp = load_progress(uid)
        await update.message.reply_text(
            f"Пройдено {comp}/{TOTAL_LESSONS} ({round(comp/TOTAL_LESSONS*100)}%)"
            if comp
            else "Не начинали"
        )
    elif text == "⭐ Избранное":
        await favorites(update, context)
    elif text == "📚 Пройденные":
        await show_completed(update, context)
    elif text == "📋 План":
        await plan(update, context)
    elif text == "💰 Токены":
        await tokens(update, context)
    elif text == "📒 Заметки":
        await update.message.reply_text(
            "/note добавить <текст>\n/note список\n/note удалить <id>"
        )
    elif text == "❓ Задать вопрос":
        await update.message.reply_text("Введите ваш вопрос:")
    elif text == "♻️ Сброс":
        from db import reset_progress

        reset_progress(uid)
        await update.message.reply_text("Прогресс сброшен.")
    else:
        await ask(update, context)


def main():
    init_db()
    start_miniapp()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("note", note_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info(f"Бот запущен. Уроков: {TOTAL_LESSONS}")
    app.run_polling()


if __name__ == "__main__":
    main()
