from telegram import Update
from telegram.ext import ContextTypes
from db import get_token_summary
from config import INITIAL_BALANCE

async def tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    tokens, cost = get_token_summary(uid)
    remain = max(0.0, INITIAL_BALANCE - cost)
    await update.message.reply_text(f"💰 Потрачено токенов: {tokens:,}\nРасходы: ${cost:.4f}\nОстаток: ~${remain:.2f}")