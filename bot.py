import os
import asyncio
import re
import yt_dlp
import traceback
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

TOKEN = "8876675492:AAEpPcm-qFDAGiQblS4bo1E3JJPayJNNEJ8"

# Progress Bar လုပ်ဆောင်ချက်
def get_progress_hook(message):
    def hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            # Telegram မှာ Message ပြန်ပြင်ပေးခြင်း
            try:
                # Async မဟုတ်တဲ့ နေရာကနေ Update လုပ်ရန်အတွက်
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(
                    message.edit_text(f"⏳ ဒေါင်းလုဒ်ဆွဲနေသည်: {p}\nခဏစောင့်ပေးပါ..."), 
                    loop
                )
            except:
                pass
    return hook

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ! YouTube MP3 Downloader Bot ပါ။\n\nလင့်ခ်ပို့လိုက်တာနဲ့ MP3 အဖြစ် ပြောင်းပေးပါမယ်။")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ အသုံးပြုနည်း:\nYouTube လင့်ခ်တစ်ခုကို Copy ကူးပြီး ဒီ Bot ထဲ ပို့လိုက်ပါ။")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot အလုပ်လုပ်နေပါတယ် (Online ရှိပါသည်)။")

def download_audio_sync(url, message):
    ydl_opts = {
        'format': 'm4a/bestaudio/ba/best',
        'outtmpl': '%(title)s.%(ext)s', 
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'socket_timeout': 60,
        'source_address': '0.0.0.0',
        'cookiefile': 'cookies.txt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [get_progress_hook(message)], # Progress Bar Hook
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace(info['ext'], 'mp3')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    match = re.search(r'(https?://[^\s]+)', text)
    
    if not match:
        await update.message.reply_text("❌ လင့်ခ်မှားနေပါသည်။")
        return

    url = match.group(0)
    # ပထမဆုံး စတင်ကြောင်း Message ပို့ခြင်း
    status_msg = await update.message.reply_text("⏳ စတင်ဒေါင်းလုဒ်ဆွဲနေပါပြီ...")
    
    try:
        loop = asyncio.get_running_loop()
        # Message ကို ပါ ထည့်ပေးလိုက်တယ်
        file_path = await loop.run_in_executor(None, download_audio_sync, url, status_msg)
        
        if os.path.exists(file_path):
            await status_msg.edit_text("✅ အောင်မြင်ပါပြီ! ပို့ပေးနေပါပြီ...")
            
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=file_name.replace('.mp3', '')
                )
            
            if os.path.exists(file_path):
                os.remove(file_path)
            await status_msg.delete()
        else:
            raise Exception("File not found.")
            
    except Exception as e:
        traceback.print_exc()
        await status_msg.edit_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).connect_timeout(60).read_timeout(60).write_timeout(60).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Bot is running...")
    app.run_polling()