# raspberry_bot.py

import telebot
from telebot.types import Message
from config import RASPBERRY_BOT_TOKEN, ADMIN_ID, DELIVERY_CHANNEL_ID

bot = telebot.TeleBot(RASPBERRY_BOT_TOKEN, parse_mode='HTML')

@bot.message_handler(func=lambda message: True, content_types=[
    'text', 'photo', 'video', 'document', 'audio', 'voice',
    'sticker', 'video_note', 'animation', 'location', 'contact'
])
def forward_everything(message: Message):
    if message.from_user.id == ADMIN_ID:
        try:
            bot.copy_message(chat_id=DELIVERY_CHANNEL_ID,
                             from_chat_id=message.chat.id,
                             message_id=message.message_id)
            bot.send_message(message.chat.id, "Delivered")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Failed to deliver message: {e}")

print("🚀 raspberry_bot is running...")
bot.infinity_polling()
