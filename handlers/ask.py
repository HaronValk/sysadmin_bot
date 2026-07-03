from telegram import Update
from telegram.ext import ContextTypes
from ai_client import ask_ai
from db import load_progress, record_token_usage

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    last = load_progress(uid)
    question = update.message.text
    await update.message.reply_text("🤔 Думаю...")
    answer, usage = ask_ai(question, last if last > 0 else None)
    if usage:
        record_token_usage(uid, usage.total_tokens, (usage.prompt_tokens*0.14 + usage.completion_tokens*0.28)/1_000_000)
    await update.message.reply_text(answer)