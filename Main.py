import os
import time
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- RENDER CANLI TUTMA ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot Aktif!"

def run_web_server():
    port = int(os.environ.get('PORT', 5000))
    app_flask.run(host='0.0.0.0', port=port)

# --- AYARLAR ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_id = int(os.environ.get("TELEGRAM_API_ID", "0"))
api_hash = os.environ.get("TELEGRAM_API_HASH", "")
bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")

bot = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
url_store = {}

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Merhaba! YouTube, Instagram, TikTok veya Pinterest linki gönder, senin için indireyim.")

@bot.on_message(filters.text & ~filters.command("start"))
async def handle_message(client, message):
    url = message.text.strip()
    if any(p in url for p in ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "pinterest.com", "pin.it"]):
        uid = str(time.time()).replace(".", "")[-8:]
        url_store[uid] = url
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 MP3 (Ses)", callback_data=f"mp3|{uid}")],
            [InlineKeyboardButton("📺 MP4 (Video)", callback_data=f"mp4|{uid}")]
        ])
        await message.reply_text("📥 Format seçin:", reply_markup=keyboard)
    else:
        await message.reply_text("❌ Desteklenmeyen link!")

@bot.on_callback_query()
async def callback_handler(client, query):
    data = query.data.split("|")
    fmt, uid = data[0], data[1]
    url = url_store.get(uid)
    if not url: return

    status = await query.message.edit_text("⏳ Hazırlanıyor...")
    out_name = f"file_{uid}"
    ydl_opts = {'restrictfilenames': True, 'noplaylist': True, 'quiet': True}

    if fmt == "mp3":
        ydl_opts.update({'format': 'bestaudio/best', 'outtmpl': f'{out_name}.%(ext)s',
                        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})
    else:
        ydl_opts.update({'format': 'best', 'outtmpl': f'{out_name}.%(ext)s'})

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            target_file = None
            for f in os.listdir():
                if f.startswith(out_name):
                    target_file = f
                    break
            
            if target_file:
                if fmt == "mp3":
                    await client.send_audio(query.message.chat.id, audio=target_file)
                else:
                    await client.send_video(query.message.chat.id, video=target_file)
                os.remove(target_file)
                await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ Hata: {str(e)[:50]}")

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    bot.run()
