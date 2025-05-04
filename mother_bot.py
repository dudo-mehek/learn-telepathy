# mother_bot.py
import telebot, random, string
from config import MOTHER_BOT_TOKEN, ADMIN_ID, WORKER_BOTS, MEDIA_HUB_CHAT_ID
from utils import store_in_database

bot = telebot.TeleBot(MOTHER_BOT_TOKEN, parse_mode='HTML')

def generate_unique_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def handle_media(message):
    if message.from_user.id != ADMIN_ID:
        return

    worker_id = random.choice(list(WORKER_BOTS.keys()))
    unique_key = generate_unique_key()

    sent = bot.forward_message(chat_id=MEDIA_HUB_CHAT_ID, from_chat_id=message.chat.id, message_id=message.message_id)
    store_in_database(unique_key, {
        "worker_id": worker_id,
        "message_id": sent.message_id,
        "media_type": message.content_type
    })

    deep_link = f"https://t.me/{worker_id}_bot?start={unique_key}"
    bot.send_message(ADMIN_ID, f"Here's your link:\n<code>{deep_link}</code>")

print("✅ Mother bot is running...")
bot.infinity_polling()