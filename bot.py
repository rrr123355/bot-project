from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction
import asyncio

# ⚠️ নিজের নতুন TOKEN বসাও (BotFather থেকে)
TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"

PASSWORD = "Sabnur123"

file_store = {}
user_waiting_password = {}
user_delete_request = {}

# 🔹 ফাইল save
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.document:
        user_id = update.effective_user.id
        file = update.message.document

        user_waiting_password[user_id] = file
        await update.message.reply_text("🔐 Please enter password to generate link:")


# 🔹 password check + link generate
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user_id = update.effective_user.id
    text = update.message.text

    # 🔴 delete confirm
    if user_id in user_delete_request:
        if text == PASSWORD:
            file_key = user_delete_request[user_id]
            if file_key in file_store:
                file_name = file_store[file_key]["file_name"]
                del file_store[file_key]

                await update.message.reply_text(
                    f"✅ File deleted!\n\n📂 {file_name}\n🔗 Link expired."
                )
            else:
                await update.message.reply_text("❌ File not found.")

        else:
            await update.message.reply_text("❌ Wrong password!")

        del user_delete_request[user_id]
        return

    # 🔹 generate link
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
            file_key = str(file_id)[-8:]

            file_store[file_key] = {
                "file_id": file_id,
                "file_name": file_name,
                "owner_id": user_id
            }

            bot_username = (await context.bot.get_me()).username
            link = f"https://t.me/{bot_username}?start={file_key}"

            keyboard = [[InlineKeyboardButton("📥 Open Link", url=link)]]

            await update.message.reply_text(
                f"✅ Authorized!\n\n📂 {file_name}\n🔗 {link}\n\nUse /delete to remove file.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            del user_waiting_password[user_id]
        else:
            await update.message.reply_text("❌ Wrong password!")


# 🔹 delete command
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user_files = {k: v for k, v in file_store.items() if v["owner_id"] == user_id}

    if not user_files:
        await update.message.reply_text("📭 No files found.")
        return

    keyboard = []
    for key, val in user_files.items():
        name = val["file_name"]
        short = name[:30] + "..." if len(name) > 30 else name
        keyboard.append([InlineKeyboardButton(short, callback_data=f"del_{key}")])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])

    await update.message.reply_text(
        "🗑 Select file to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# 🔹 button handler
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

        if key in file_store:
            if file_store[key]["owner_id"] == user_id:
                file_name = file_store[key]["file_name"]

                user_delete_request[user_id] = key

                await query.edit_message_text(
                    f"🔐 Enter password to delete:\n\n📂 {file_name}"
                )
            else:
                await query.edit_message_text("❌ Not your file")
        else:
            await query.edit_message_text("❌ File not found")


# 🔹 start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name

    if context.args:
        key = context.args[0]

        if key in file_store:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(1)

            await update.message.reply_text(f"👋 {user}\n📦 Sending file...")
            await update.message.reply_document(file_store[key]["file_id"])
        else:
            await update.message.reply_text("❌ File expired")
    else:
        await update.message.reply_text(
            "🤖 Send file → enter password → get link\n\nUse /delete to remove files"
        )


# 🔹 run app
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
app.add_handler(CallbackQueryHandler(button_callback))

print("✅ Bot running...")
app.run_polling()
