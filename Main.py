import os
import time
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- RENDER CANLI TUTMA ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot 7/24 Aktif!"

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

# --- DESTEKLENEN PLATFORMLAR ---
def is_supported(url):
    platforms = ["youtube.com", "youtu.be", "instagram.com", "tiktok.com", "pinterest.com", "pin.it"]
    return any(p in url for p in platforms)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "🚀 **Çok Amaçlı İndirici Bot Hazır!**\n\n"
        "Aşağıdaki platformlardan link gönderebilirsin:\n"
        "• YouTube & Shorts\n"
        "• Instagram Reels\n"
        "• TikTok (Logosuz)\n"
        "• Pinterest Video\n\n"
        "⚡ _Sadece linki yapıştır ve bekle!_"
    )

@bot.on_message(filters.text & ~filters.command("start"))
async def handle_message(client, message):
    url = message.text.strip()
    
    if is_supported(url):
        uid = str(time.time()).replace(".", "")[-8:]
        url_store[uid] = url
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 MP3 (Ses)", callback_data=f"mp3|{uid}")],
            [InlineKeyboardButton("📺 MP4 (Video)", callback_data=f"mp4|{uid}")]
        ])
        await message.reply_text("📥 Hangi formatta indirmek istersiniz?", reply_markup=keyboard)
    else:
        await message.reply_text("❌ Desteklenmeyen bir link gönderdiniz. Lütfen geçerli bir URL deneyin.")

@bot.on_callback_query()
async def callback_handler(client, query):
    data = query.data.split("|")
    format_choice = data[0]
    uid = data[1]
    url = url_store.get(uid)

    if not url:
        await query.message.edit_text("❌ Oturum süresi doldu. Lütfen linki tekrar gönderin.")
        return

    status_msg = await query.message.edit_text(f"⏳ {format_choice.upper()} hazırlanıyor... Lütfen bekleyin.")

    output_filename = f"file_{uid}"
    
    # Platforma göre özel ayarlar
    ydl_opts = {
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    if format_choice == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': f'{output_filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # TikTok ve Pinterest için en iyi videoyu seç
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{output_filename}.%(ext)s',
            'merge_output_format': 'mp4',
        })

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # TikTok/Pinterest gibi platformlarda hata payını düşürmek için extract_info
            info = ydl.extract_info(url, download=True)
            
            # İndirilen dosyayı kontrol et (farklı uzantılar için)
            downloaded_file = None
            for f in os.listdir():
                if f.startswith(output_filename):
                    downloaded_file = f
                    break
            
            if not downloaded_file:
                raise Exception("Dosya indirilemedi.")

            if format_choice == "mp3":
                await client.send_audio(
                    chat_id=query.message.chat.id, 
                    audio=downloaded_file, 
                    caption="✅ Ses dosyası hazır!"
                )
            else:
                await client.send_video(
                    chat_id=query.message.chat.id, 
                    video=downloaded_file, 
                    caption="✅ Video hazır!"
                )

            # Temizlik
            os.remove(downloaded_file)
            await status_msg.delete()

    except Exception as e:
        logger.error(f"HATA: {str(e)}")
        await status_msg.edit_text(f"❌ Bir hata oluştu.\nDetay: `{str(e)[:100]}`")

if __name__ == "__main__":
    # Flask sunucusunu başlat (Render için)
    Thread(target=run_web_server).start()
    
    # Botu başlat
    logger.info("Bot Aktif ve Link Bekliyor...")
    bot.run()
