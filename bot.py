import os
import cv2
import numpy as np
from gtts import gTTS
from moviepy.editor import
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from flask import Flask
import threading

# Create required folders
for folder in ["static", "logs"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

def text_to_speech(text, output_audio):
    tts = gTTS(text, lang='en')
    tts.save(output_audio)

def create_text_image(text, image_size=(1280, 720), font_size=50):
    image = Image.new("RGB", image_size, (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text_width, text_height = draw.textsize(text, font=font)
    position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 2)
    draw.text(position, text, font=font, fill=(255, 255, 255))
    
    image_path = "static/text_image.png"
    image.save(image_path)
    return image_path

def generate_video_from_text(text, output_video="static/output.mp4", duration=5, fps=30):
    image_path = create_text_image(text)
    audio_path = "static/output_audio.mp3"
    text_to_speech(text, audio_path)
    
    image = cv2.imread(image_path)
    height, width, layers = image.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    for _ in range(duration * fps):
        video.write(image)
    
    video.release()
    
    final_clip = VideoFileClip(output_video)
    audio_clip = AudioFileClip(audio_path)
    final_clip = final_clip.set_audio(audio_clip)
    final_clip.write_videofile("static/final_output.mp4", codec="libx264", fps=fps)

    os.remove(output_video)
    os.remove(image_path)
    os.remove(audio_path)
    
    return "static/final_output.mp4"

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me a text message, and I'll convert it into a video!")

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    video_path = generate_video_from_text(text)
    update.message.reply_video(video=open(video_path, "rb"))
    os.remove(video_path)

def run_telegram_bot():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    updater.idle()

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running!"

def start_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    run_telegram_bot()
