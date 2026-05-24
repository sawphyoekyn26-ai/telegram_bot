import os
import asyncio
import re
import yt_dlp
import traceback
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# Bot Token ကို Variables ထဲကနေ ယူတာ ပိုကောင်းပါတယ် (သို့မဟုတ်) တိုက်ရိုက်ထည့်ပါ
TOKEN = os.getenv("8876675492:AAEpPcm-qFDAGiQblS4bo1E3JJPayJNNEJ8")

def get_progress_hook(message):
    def hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            try:
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(
                    message.edit_text(f"⏳ ဒေါင်းလုဒ်ဆွဲနေသည်: {p}\nခဏစောင့်ပေးပါ..."), 
                    loop
                )
            except:
                pass
    return hook

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ! YouTube MP3 Downloader Bot ပါ။\n\nYouTube လင့်ခ်ပို့ပေးလိုက်ပါဗျာ။")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ အသုံးပြုနည်း:\nYouTube လင့်ခ်ကို ဒီတိုင်း ပို့ပေးလိုက်ရုံပါပဲ။")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot အလုပ်လုပ်နေပါတယ် (Railway Cloud ပေါ်တွင်)။")

def download_audio_sync(url, message):
    ydl_opts = {
        'format': 'm4a/bestaudio/ba/best', # ပိုမိုကောင်းမွန်သော Format ရှာဖွေမှု
        'outtmpl': '%(title)s.%(ext)s', 
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [get_progress_hook(message)],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace(info['ext'], 'mp3')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    match = re.search(r'(https?://[^\s]+)', text)
    
    if not match:
        return

    url = match.group(0)
    status_msg = await update.message.reply_text("⏳ စတင်လုပ်ဆောင်နေပါပြီ...")
    
    try:
        loop = asyncio.get_running_loop()
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
            raise Exception("ဖိုင်ကို ရှာမတွေ့ပါ။")
            
    except Exception as e:
        traceback.print_exc()
        await status_msg.edit_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    # drop_pending_updates=True ကိုထည့်ထားတဲ့အတွက် Conflict ဖြစ်တာ သက်သာစေပါမယ်
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)