from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatAction
import asyncio

TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"

# 👉 এখানে password সেট করো
PASSWORD = "Sabnur123"

# temp storage
file_store = {}
user_waiting_password = {}

# 🔹 যখন file পাঠাবে
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.document

    if file:
        # user কে password দিতে বলবে
        user_waiting_password[user_id] = file

        await update.message.reply_text(
            "🔐 Please enter password to generate link:"
        )

# 🔹 password check
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_waiting_password:
        if text == PASSWORD:
            file = user_waiting_password[user_id]

            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(1)

            file_id = file.file_id
            file_name = file.file_name
            file_key = str(file_id)[-8:]

            file_store[file_key] = file_id

            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start={file_key}"

            keyboard = [
                [InlineKeyboardButton("📥 Open Link", url=link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ <b>Authorized!</b>\n\n"
                f"📂 <b>{file_name}</b>\n"
                f"🔗 <b>Link:</b>\n{link}",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            del user_waiting_password[user_id]

        else:
            await update.message.reply_text("❌ Wrong password!")

# 🔹 start command (file send)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if context.args:
        key = context.args[0]

        if key in file_store:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
            await asyncio.sleep(2)

            await update.message.reply_text(f"👋 Hello {user}\n📦 Sending your file...")

            await update.message.reply_document(file_store[key])
        else:
            await update.message.reply_text("❌ File not found or expired")

    else:
        await update.message.reply_text(
            "🤖 Welcome!\n\nSend file + password to get shareable link 🔐"
        )

# app
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))

print("🔐 Bot running with password system...")
app.run_polling()
