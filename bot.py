from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.constants import ChatAction
import asyncio
import firebase_admin
from firebase_admin import credentials, db
import os, json

TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"
PASSWORD = "Sabnur123"

firebase_json = os.environ.get("FIREBASE_KEY")

if firebase_json:
    cred_dict = json.loads(firebase_json)
    cred = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'YOUR_DB_URL'
    })

    ref = db.reference("files")
else:
    ref = None

user_waiting_password = {}

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.document

    if file:
        user_waiting_password[user_id] = file
        await update.message.reply_text("🔐 Enter password:")

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_waiting_password:
        if text == PASSWORD:
            file = user_waiting_password[user_id]

            file_id = file.file_id
            file_name = file.file_name
            file_key = str(file_id)[-8:]

            if ref:
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        key = context.args[0]

        file_id = ref.child(key).get() if ref else None

        if file_id:
            await update.message.reply_text("📦 Sending file...")
            await update.message.reply_document(file_id)
        else:
            await update.message.reply_text("❌ File not found")
    else:
        await update.message.reply_text("🤖 Send file + password")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))

print("🔥 Bot running...")
app.run_polling()
