from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction
import asyncio

TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"  # 🔴 এখানে নতুন token বসাও

PASSWORD = "Sabnur123"

file_store = {}
user_waiting_password = {}
user_delete_request = {}

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.document:
        user_id = update.effective_user.id
        file = update.message.document
        user_waiting_password[user_id] = file
        await update.message.reply_text("🔐 Please enter password:")


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.effective_user.id
    text = update.message.text if update.message else ""

    if user_id in user_delete_request:
        if text == PASSWORD:
            key = user_delete_request[user_id]
            if key in file_store:
                name = file_store[key]["file_name"]
                del file_store[key]
                await update.message.reply_text(f"✅ Deleted\n📂 {name}")
            else:
                await update.message.reply_text("❌ Not found")
        else:
            await update.message.reply_text("❌ Wrong password")

        del user_delete_request[user_id]
        return

    if user_id in user_waiting_password:
        if text == PASSWORD:
            file = user_waiting_password[user_id]

            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(1)

            file_id = file.file_id
            file_name = file.file_name
            key = str(file_id)[-8:]

            file_store[key] = {
                "file_id": file_id,
                "file_name": file_name,
                "owner_id": user_id
            }

            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start={key}"

            keyboard = [[InlineKeyboardButton("📥 Open Link", url=link)]]

            await update.message.reply_text(
                f"✅ {file_name}\n🔗 {link}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            del user_waiting_password[user_id]
        else:
            await update.message.reply_text("❌ Wrong password")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    files = {k: v for k, v in file_store.items() if v["owner_id"] == user_id}

    if not files:
        await update.message.reply_text("📭 No files")
        return

    keyboard = []
    for k, v in files.items():
        name = v["file_name"]
        keyboard.append([InlineKeyboardButton(name[:30], callback_data=f"del_{k}")])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])

    await update.message.reply_text(
        "🗑 Select file:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "del_cancel":
        await query.edit_message_text("❌ Cancelled")
        return

    if data.startswith("del_"):
        key = data.split("_")[1]

        if key in file_store and file_store[key]["owner_id"] == user_id:
            user_delete_request[user_id] = key
            await query.edit_message_text("🔐 Enter password to delete")
        else:
            await query.edit_message_text("❌ Error")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        key = context.args[0]

        if key in file_store:
            await update.message.reply_document(file_store[key]["file_id"])
        else:
            await update.message.reply_text("❌ Expired")
    else:
        await update.message.reply_text("🤖 Send file → password → get link")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
app.add_handler(CallbackQueryHandler(button_callback))

print("✅ Bot running...")
app.run_polling()
