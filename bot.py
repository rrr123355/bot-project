from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction
import asyncio

TOKEN = "8529913372:AAFzMAqPNWlQFhMjHAoxDqTkzWngHGJtQkQ"

# 👉 পাসওয়ার্ড সেট করো
PASSWORD = "Sabnur123"

# টেম্প স্টোরেজ: {file_key: {"file_id": id, "file_name": name, "owner_id": user_id}}
file_store = {}
user_waiting_password = {}
user_delete_request = {}  # {user_id: file_key} - ডিলিটের জন্য অপেক্ষমাণ

# 🔹 ফাইল পাঠালে
async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    file = update.message.document

    if file:
        user_waiting_password[user_id] = file
        await update.message.reply_text("🔐 Please enter password to generate link:")

# 🔹 পাসওয়ার্ড চেক করে লিংক জেনারেট (এবং ডিলিট কনফার্ম)
async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # প্রথমে চেক করি ডিলিট রিকোয়েস্ট আছে কিনা
    if user_id in user_delete_request:
        if text == PASSWORD:
            file_key = user_delete_request[user_id]
            if file_key in file_store:
                file_name = file_store[file_key]["file_name"]
                del file_store[file_key]
                await update.message.reply_text(
                    f"✅ **File deleted successfully!**\n\n"
                    f"📂 {file_name}\n"
                    f"🔗 The link has expired.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ File not found or already expired.")
            del user_delete_request[user_id]
        else:
            await update.message.reply_text("❌ Wrong password! Deletion cancelled.")
            del user_delete_request[user_id]
        return

    # ফাইল জেনারেটের জন্য পাসওয়ার্ড চেক
    if user_id in user_waiting_password:
        if text == PASSWORD:
            file = user_waiting_password[user_id]

            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
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
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ <b>Authorized!</b>\n\n"
                f"📂 <b>{file_name}</b>\n"
                f"🔗 <b>Link:</b>\n{link}\n\n"
                f"🗑 To delete any file, use /delete",
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            del user_waiting_password[user_id]
        else:
            await update.message.reply_text("❌ Wrong password!")

# 🔹 ডিলিট কমান্ড - সব ফাইলের লিস্ট দেখাবে
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # ইউজারের সব ফাইল বের করো
    user_files = {k: v for k, v in file_store.items() if v["owner_id"] == user_id}
    
    if not user_files:
        await update.message.reply_text("📭 You have no files to delete.")
        return
    
    # বাটন তৈরি করো
    keyboard = []
    for key, val in user_files.items():
        # ফাইলের নাম ছোট করে দেখাবে (max 30 character)
        short_name = val['file_name'][:30] + "..." if len(val['file_name']) > 30 else val['file_name']
        keyboard.append([InlineKeyboardButton(f"📄 {short_name}", callback_data=f"del_{key}")])
    
    # ক্যানসেল বাটন
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🗑 **Select the file you want to delete:**\n\n"
        "Click on a file, then enter your password to confirm deletion.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# 🔹 বাটন ক্লিক হ্যান্ডলার
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "del_cancel":
        await query.edit_message_text("❌ Deletion cancelled.")
        return
    
    if data.startswith("del_"):
        file_key = data.split("_")[1]
        
        if file_key in file_store:
            if file_store[file_key]["owner_id"] == user_id:
                file_name = file_store[file_key]["file_name"]
                # ডিলিট রিকোয়েস্ট সেভ করি
                user_delete_request[user_id] = file_key
                await query.edit_message_text(
                    f"🔐 **Password required to delete:**\n\n"
                    f"📂 {file_name}\n\n"
                    f"Please type your password to confirm deletion.",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("❌ You cannot delete this file.")
        else:
            await query.edit_message_text("❌ File not found or already expired.")

# 🔹 start কমান্ড (লিংক থেকে ক্লিক করলে ফাইল পাঠাবে)
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
            await update.message.reply_text("❌ File not found or expired")
    else:
        await update.message.reply_text(
            "🤖 **Welcome to File Share Bot!**\n\n"
            "📤 **How to use:**\n"
            "1️⃣ Send me any file\n"
            "2️⃣ Enter the password\n"
            "3️⃣ Get a shareable link\n\n"
            "🗑 **Delete files:**\n"
            "Type /delete to see all your files\n"
            "Click on any file → Enter password → File deleted\n\n"
            "🔗 Others can download using your link",
            parse_mode="Markdown"
        )

# অ্যাপ রান
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("delete", delete_command))
app.add_handler(MessageHandler(filters.Document.ALL, save_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_password))
app.add_handler(CallbackQueryHandler(button_callback))

print("✅ Bot running - Password required for deletion...")
app.run_polling()
