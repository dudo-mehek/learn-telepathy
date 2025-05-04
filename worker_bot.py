# worker_bot.py
import telebot
import sys
import string
import random
import time
import threading
import json
from datetime import datetime  # Added for timestamp in retry message
from config import WORKER_BOTS, ADMIN_ID, MEDIA_HUB_CHAT_ID, BACKUP_STATION_CHAT_ID, BACKUP_JOIN_LINK
from utils import store_in_database, get_from_database

WORKER_ID = sys.argv[1]
BOT_TOKEN = WORKER_BOTS[WORKER_ID]
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

def generate_unique_key():
    return ''.join(random.choices(string.ascii_letters + string.digits + "-_", k=32))

def delete_message_later(chat_id, message_id, delay=1800):
    def delete():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=delete).start()

# Only respond to admin when media is sent
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def handle_admin_media(message):
    if message.from_user.id != ADMIN_ID:
        return

    unique_key = generate_unique_key()

    # Forward to media hub (for backup) with message indicating the bot name
    bot_name = bot.get_me().username  # Get the bot's name
    message_with_bot_name = f"Media sent by {bot_name}\n\n"
    forwarded = bot.forward_message(chat_id=MEDIA_HUB_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)

    # Send the message with bot info to the media hub
    bot.send_message(MEDIA_HUB_CHAT_ID, message_with_bot_name)

    # Store mapping in the database
    store_in_database(unique_key, {
        "worker_id": WORKER_ID,
        "message_id": forwarded.message_id,
        "media_type": message.content_type
    })

    # Reply with deep link
    bot.send_message(ADMIN_ID, f"Here's your link:\n<code>https://t.me/{WORKER_ID}_bot?start={unique_key}</code>")

# Respond to users via deep link
@bot.message_handler(commands=['start'])
def start_handler(message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "❌ Invalid link.")
        return

    key = parts[1]
    info = get_from_database(key)

    if not info or info.get("worker_id") != WORKER_ID:
        bot.send_message(message.chat.id, "❌ Invalid or expired link.")
        return

    # Check if user is a member of the backup group
    try:
        member = bot.get_chat_member(BACKUP_STATION_CHAT_ID, message.from_user.id)
        if member.status not in ['member', 'administrator', 'creator']:
            raise Exception("Not a member")
    except:
        # Ask to join group
        join_button = telebot.types.InlineKeyboardMarkup()
        join_button.row(
            telebot.types.InlineKeyboardButton("✅ Join the Group", url=BACKUP_JOIN_LINK),
            telebot.types.InlineKeyboardButton("🔄 Try Again", callback_data=f"retry:{key}")
        )
        bot.send_message(message.chat.id, "❗ You must join the Backup Station group to access this file.", reply_markup=join_button)
        return

    # Serve media
    try:
        sent = bot.copy_message(chat_id=message.chat.id, from_chat_id=MEDIA_HUB_CHAT_ID, message_id=info["message_id"])
        bot.send_message(message.chat.id, "The file will automatically delete in 30 mins.")
        delete_message_later(message.chat.id, sent.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to send media: {e}")

# Retry button handler (fully re-validates group membership)
@bot.callback_query_handler(func=lambda call: call.data.startswith("retry:"))
def retry_deep_link(call):
    user_id = call.from_user.id
    key = call.data.split(":", 1)[1]
    info = get_from_database(key)

    if not info or info.get("worker_id") != WORKER_ID:
        bot.answer_callback_query(call.id, "❌ Invalid or expired link.", show_alert=True)
        return

    try:
        member = bot.get_chat_member(BACKUP_STATION_CHAT_ID, user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            raise Exception("Not a member")
    except:
        join_button = telebot.types.InlineKeyboardMarkup()
        join_button.row(
            telebot.types.InlineKeyboardButton("✅ Join the Group", url=BACKUP_JOIN_LINK),
            telebot.types.InlineKeyboardButton("🔄 Try Again", callback_data=f"retry:{key}")
        )
        # ✅ Updated to avoid "message is not modified" error
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        bot.edit_message_text(f"❗ You must join the Backup group to access this file.\n\nUpdated: {timestamp}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=join_button
        )
        return

    # Serve media
    try:
        sent = bot.copy_message(chat_id=user_id, from_chat_id=MEDIA_HUB_CHAT_ID, message_id=info["message_id"])
        bot.send_message(user_id, "The file will automatically delete in 30 mins.")
        delete_message_later(user_id, sent.message_id)
    except Exception as e:
        bot.send_message(user_id, f"❌ Failed to send media: {e}")

print(f"✅ {WORKER_ID} bot is running...")
bot.infinity_polling()
