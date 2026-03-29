import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
from flask import Flask
from threading import Thread

# --- RENDER İÇİN CANLI TUTMA SİSTEMİ ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Aktif!"

def run_web_server():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# --- BOT AYARLARI ---
API_ID = int(os.environ.get("TELEGRAM_API_ID", 0))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Merhaba! Bana bir YouTube, Instagram veya TikTok linki gönder, senin için indireyim.")

@bot.on_message(filters.regex(r"http"))
async def download_video(client, message: Message):
    url = message.text
    status = await message.reply_text("⏳ Videon hazırlanıyor, lütfen bekle...")
    
    # DOSYA İSMİ HATASINI ÇÖZEN KRİTİK AYARLAR
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s', # Dosya ismi her zaman 'video' olacak
        'noplaylist': True,
        'restrictfilenames': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Eğer video.mp4 değilse, gerçek ismi bulalım
            actual_filename = "video.mp4"
            if not os.path.exists(actual_filename):
                # Bazı durumlarda uzantı farklı olabilir (.mkv gibi)
                for file in os.listdir():
                    if file.startswith("video."):
                        actual_filename = file
                        break

        await message.reply_video(video=actual_filename, caption="✅ İşte videon!")
        os.remove(actual_filename) # Sunucuda yer kaplamasın diye siliyoruz
        await status.delete()
        
    except Exception as e:
        await status.edit(f"❌ Bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    # Web server'ı başlat
    Thread(target=run_web_server).start()
    # Botu çalıştır
    bot.run()
