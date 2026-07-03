from telegram import Update
from telegram.ext import ContextTypes
from db import load_progress, get_favorite_ids
from lessons_loader import TOTAL_LESSONS
from keyboards import list_keyboard

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 План:", reply_markup=list_keyboard(list(range(1, TOTAL_LESSONS+1)), nav_prefix="plan_"))

async def favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    favs = get_favorite_ids(uid)
    if favs:
        await update.message.reply_text("⭐ Избранное:", reply_markup=list_keyboard(favs, nav_prefix="fav_page_"))
    else:
        await update.message.reply_text("Пусто")

async def completed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    completed = load_progress(uid)
    if completed:
        await update.message.reply_text("📚 Пройденные:", reply_markup=list_keyboard(list(range(1, completed+1)), nav_prefix="completed_page_"))
    else:
        await update.message.reply_text("Нет пройденных")