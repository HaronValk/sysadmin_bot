from telegram import Update
from telegram.ext import ContextTypes
from db import add_note, get_notes, delete_note

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("📒 /note добавить <текст>\n/note список\n/note удалить <id>")
        return
    action = args[0].lower()
    if action == "добавить":
        text = " ".join(args[1:])
        if not text: await update.message.reply_text("Укажи текст."); return
        add_note(uid, text)
        await update.message.reply_text("✅ Сохранено.")
    elif action == "список":
        notes = get_notes(uid)
        if not notes: await update.message.reply_text("Заметок нет."); return
        lines = [f"#{n[0]} [{n[2]}] {n[1]}" for n in notes]
        await update.message.reply_text("📒 Твои заметки:\n\n" + "\n".join(lines))
    elif action == "удалить":
        try:
            nid = int(args[1])
            delete_note(uid, nid)
            await update.message.reply_text("🗑️ Удалено.")
        except (IndexError, ValueError):
            await update.message.reply_text("Укажи ID заметки.")
    else:
        await update.message.reply_text("Неизвестное действие.")