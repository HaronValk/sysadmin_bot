from telegram import Update
from telegram.ext import ContextTypes
from db import (
    get_cached_lesson,
    load_progress,
    save_progress,
    complete_project_step,
    get_completed_project_steps,
    get_project_track,
    set_project_track,
)
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
    lesson = LESSONS[lid]
    practice_text = lesson.get("practice", "Задание отсутствует.")
    await query.message.reply_text(
        f"📝 Задание к уроку {lid}: {lesson['topic']}\n\n{practice_text}"
    )


async def show_project_step(query, lid):
    uid = query.from_user.id
    track = get_project_track(uid)
    lesson = LESSONS[lid]

    if track == "global":
        step_text = lesson.get("project_step_global", lesson.get("project_step_ru", ""))
        track_name = "🌍 InfraProsper (Global)"
    else:
        step_text = lesson.get("project_step_ru", lesson.get("project_step_global", ""))
        track_name = "🇷🇺 УралТехСервис (РФ)"

    if not step_text:
        await query.message.reply_text("Для этого урока нет шага проекта.")
        return

    complete_project_step(uid, lid)
    completed = get_completed_project_steps(uid)
    completed_text = []
    for l in completed:
        ls = LESSONS[l]
        step = ls.get(f"project_step_{track}", ls.get(f"project_step_ru", ""))
        if step:
            completed_text.append(f"✅ Урок {l}: {step[:100]}...")

    total = sum(
        1
        for l in LESSONS
        if LESSONS[l].get(f"project_step_{track}") or LESSONS[l].get(f"project_step_ru")
    )
    progress = len(completed_text)

    text = f"🏗️ Проект: {track_name}\n"
    text += f"📊 Прогресс: {progress} из ~{total} шагов\n\n"
    text += f"📌 Текущий шаг (урок {lid}):\n{step_text}\n\n"
    if completed_text:
        text += "Последние выполненные шаги:\n" + "\n".join(completed_text[-3:])
    text += "\n\n🔄 Переключить трек: /project ru или /project global"

    await query.message.reply_text(text)


async def handle_project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args

    if not args:
        track = get_project_track(uid)
        track_name = (
            "🌍 InfraProsper (Global)" if track == "global" else "🇷🇺 УралТехСервис (РФ)"
        )
        await update.message.reply_text(
            f"Текущий трек: {track_name}\n\n"
            f"Доступные треки:\n"
            f"/project ru — 🇷🇺 УралТехСервис (РФ)\n"
            f"/project global — 🌍 InfraProsper (Global)"
        )
        return

    track = args[0].lower()
    if track in ("ru", "russia", "рф"):
        set_project_track(uid, "ru")
        await update.message.reply_text("✅ Выбран трек: 🇷🇺 УралТехСервис (РФ)")
    elif track in ("global", "world", "мир"):
        set_project_track(uid, "global")
        await update.message.reply_text("✅ Выбран трек: 🌍 InfraProsper (Global)")
    else:
        await update.message.reply_text(
            "Неизвестный трек. Используй: /project ru или /project global"
        )
