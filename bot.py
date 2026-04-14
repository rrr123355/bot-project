import firebase_admin
from firebase_admin import credentials, db

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatAction
import asyncio

TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"
PASSWORD = "Sabnur123"

# 🔥 Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://tic-tac-toe-5a407-default-rtdb.firebaseio.com/'
})

ref = db.reference("files")

user_waiting_password = {}

# 🔹 file receive
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.document

    if file:
        user_waiting_password[user_id] = file
        await update.message.reply_text("🔐 Enter password:")

# 🔹 password check
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_waiting_password:
        if text == PASSWORD:
            file = user_waiting_password[user_id]

            file_id = file.file_id
            file_name = file.file_name
            file_key = str(file_id)[-8:]

            # 🔥 Firebase-এ save
            ref.child(file_key).set(file_id)

            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start={file_key}"

            keyboard = [[InlineKeyboardButton("📥 Open Link", url=link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ Authorized!\n\n📂 {file_name}\n🔗 {link}",
                reply_markup=reply_markup
            )

            del user_waiting_password[user_id]

        else:
            await update.message.reply_text("❌ Wrong password!")

# 🔹 start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if context.args:
        key = context.args[0]

        # 🔥 Firebase থেকে load
        file_id = ref.child(key).get()

        if file_id:
            await update.message.reply_text(f"📦 Sending file...")
            await update.message.reply_document(file_id)
        else:
            await update.message.reply_text("❌ File not found")

    else:
        await update.message.reply_text("🤖 Send file + password")

# app
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))

print("🔥 Bot running with Firebase...")
app.run_polling()