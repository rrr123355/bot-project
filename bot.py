from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction
import asyncio
import json
import os

TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"
PASSWORD = "Sabnur123"

# Storage: {file_key: {"file_id": id, "file_name": name, "owner_id": user_id}}
file_store = {}
user_waiting_password = {}

DATA_FILE = "file_data.json"

# Load & Save data
def load_data():
    global file_store
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            file_store = json.load(f)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(file_store, f, indent=4)

load_data()

# 🔹 Save file (ask for password)
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.document

    if file:
        user_waiting_password[user_id] = file
        await update.message.reply_text(
            "🔐 Please enter the password to generate link:"
        )

# 🔹 Check password & generate link
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_waiting_password:
        if text == PASSWORD:
            file = user_waiting_password[user_id]
            file_id = file.file_id
            file_name = file.file_name
            file_key = str(file_id)[-8:]

            file_store[file_key] = {
                "file_id": file_id,
                "file_name": file_name,
                "owner_id": user_id
            }
            save_data()

            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start={file_key}"

            keyboard = [
                [InlineKeyboardButton("📥 Download Link", url=link)],
                [InlineKeyboardButton("🗑 Delete File", callback_data=f"del_{file_key}"),
                 InlineKeyboardButton("✏️ Edit File", callback_data=f"edit_{file_key}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ <b>File Saved!</b>\n\n"
                f"📂 <b>{file_name}</b>\n"
                f"🔗 <b>Link:</b>\n{link}\n\n"
                f"⚠️ Only you can delete/edit this file.",
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            del user_waiting_password[user_id]
        else:
            await update.message.reply_text("❌ Wrong password!")

# 🔹 Start command (file download)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if context.args:
        key = context.args[0]
        if key in file_store:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(1)
            await update.message.reply_text(f"👋 Hello {user}\n📦 Sending your file...")
            await update.message.reply_document(file_store[key]["file_id"])
        else:
            await update.message.reply_text("❌ File not found or expired.")
    else:
        await update.message.reply_text(
            "🤖 Welcome to the bot!\n\n"
            "📤 Send a file → Enter password → Get download link.\n"
            "📋 Commands:\n"
            "/myfiles - View your files\n"
            "/help - Get help"
        )

# 🔹 Button handler (Delete/Edit)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    if data.startswith("del_"):
        key = data.split("_")[1]
        if key in file_store and file_store[key]["owner_id"] == user_id:
            del file_store[key]
            save_data()
            await query.edit_message_text("🗑 File deleted successfully.")
        else:
            await query.edit_message_text("❌ You cannot delete this file.")

    elif data.startswith("edit_"):
        key = data.split("_")[1]
        if key in file_store and file_store[key]["owner_id"] == user_id:
            context.user_data["edit_key"] = key
            await query.edit_message_text("✏️ Please send the new file to replace the old one.")
        else:
            await query.edit_message_text("❌ You cannot edit this file.")

# 🔹 Edit file (replace)
async def edit_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if "edit_key" in context.user_data:
        key = context.user_data["edit_key"]
        if key in file_store and file_store[key]["owner_id"] == user_id:
            new_file = update.message.document
            if new_file:
                file_store[key]["file_id"] = new_file.file_id
                file_store[key]["file_name"] = new_file.file_name
                save_data()
                await update.message.reply_text("✅ File updated successfully!")
                del context.user_data["edit_key"]
            else:
                await update.message.reply_text("⚠️ Please send a valid document.")
        else:
            await update.message.reply_text("❌ Permission denied.")
    else:
        await update.message.reply_text("No edit request found. Use /myfiles to see your files.")

# 🔹 My files list
async def my_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_files = {k: v for k, v in file_store.items() if v["owner_id"] == user_id}

    if not user_files:
        await update.message.reply_text("📭 You have no files.")
        return

    text = "📋 **Your file list:**\n\n"
    for key, val in user_files.items():
        text += f"📄 {val['file_name']}\n🔑 `{key}`\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# 🔹 Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *How to use:*\n\n"
        "1️⃣ Send a file\n"
        "2️⃣ Enter password\n"
        "3️⃣ Get Delete/Edit options\n"
        "4️⃣ Use /myfiles to view your files\n"
        "5️⃣ Others can download using `start filekey`",
        parse_mode="Markdown"
    )

# 🔹 Run app
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("myfiles", my_files))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.Document.ALL & ~filters.COMMAND, edit_file))  # Edit file
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
app.add_handler(CallbackQueryHandler(button_callback))

print("✅ Premium bot running with Delete, Edit & My Files features...")
app.run_polling()
