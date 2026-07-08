from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from config import MINI_APP_URL, LESSONS_PER_PAGE
from lessons_loader import LESSONS, TOTAL_LESSONS
from db import is_favorite


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["▶️ Начать обучение", "📊 Прогресс"],
            ["⭐ Избранное", "📚 Пройденные"],
            ["📋 План", "💰 Токены"],
            ["❓ Задать вопрос", "📒 Заметки"],
            ["♻️ Сброс"],
        ],
        resize_keyboard=True,
    )


def lesson_keyboard(lid, uid, part=1, total=1):
    rows = []
    # Строка 1: Далее + WebApp
    row1 = []
    if total > 1 and part < total:
        row1.append(
            InlineKeyboardButton("📄 Далее", callback_data=f"part_{lid}_{part+1}")
        )
    row1.append(
        InlineKeyboardButton(
            "📱 WebApp", web_app=WebAppInfo(url=f"{MINI_APP_URL}/lesson/{lid}")
        )
    )
    if row1:
        rows.append(row1)

    # Строка 2: Назад / Вперёд
    row2 = []
    if lid > 1:
        row2.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{lid-1}"))
    if lid < TOTAL_LESSONS:
        row2.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"next_{lid+1}"))
    if row2:
        rows.append(row2)

    # Строка 3: Избранное + Заметки
    row3 = []
    fav = is_favorite(uid, lid)
    row3.append(
        InlineKeyboardButton(
            "⭐ Убрать" if fav else "☆ В избранное",
            callback_data=f"{'unfav' if fav else 'fav'}_{lid}",
        )
    )
    row3.append(InlineKeyboardButton("📒 Заметки", callback_data=f"note_{lid}"))
    rows.append(row3)

    # Строка 4: Задание
    rows.append([InlineKeyboardButton("📝 Задание", callback_data=f"practice_{lid}")])

    # Строка 5: Проект (если есть шаг)
    from db import get_project_track

    # В функции lesson_keyboard:
    track = get_project_track(uid)
    if LESSONS[lid].get("project_step_ru") or LESSONS[lid].get("project_step_global"):
        rows.append(
            [
                InlineKeyboardButton(
                    "🏗️ Проект",
                    web_app=WebAppInfo(
                        url=f"{MINI_APP_URL}/project/{lid}?track={track}"
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(rows)


def list_keyboard(items, page=0, prefix="open_", nav_prefix="list_"):
    start = page * LESSONS_PER_PAGE
    end = start + LESSONS_PER_PAGE
    page_items = items[start:end]
    btns = [
        [
            InlineKeyboardButton(
                f"{lid}. {LESSONS[lid]['topic']}", callback_data=f"{prefix}{lid}"
            )
        ]
        for lid in page_items
    ]
    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton("◀ Назад", callback_data=f"{nav_prefix}{page-1}")
        )
    if end < len(items):
        nav.append(
            InlineKeyboardButton("Вперёд ▶", callback_data=f"{nav_prefix}{page+1}")
        )
    if nav:
        btns.append(nav)
    return InlineKeyboardMarkup(btns)
