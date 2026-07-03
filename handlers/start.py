from telegram import Update
from telegram.ext import ContextTypes
from keyboards import main_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Я бот-учитель. Нажми ▶️ Начать обучение", reply_markup=main_keyboard())