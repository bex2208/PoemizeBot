# ===== Imports =====
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from google import genai
from google.genai import types
import os
import requests as req

# ===== Environment Variables =====
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot, None, workers=0)

# ===== Flask app =====
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Poemize Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "ok"

# ===== Gemini prompt =====
def generate_poem(photo_url: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Download the image bytes from Telegram
    image_data = req.get(photo_url).content

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
            "Write a short and fun poem (3-4 lines) describing this picture. "
            "Make it creative, kid-friendly, and vivid. Only respond with the poem text."
        ]
    )
    return response.text.strip()

# ===== Telegram photo handler =====
def handle_photo(update: Update, context):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file = bot.get_file(file_id)
        photo_url = file.file_path
        poem = generate_poem(photo_url)
        update.message.reply_text(poem)

# Register handler
dp.add_handler(MessageHandler(Filters.photo, handle_photo))

# ===== Run Flask app =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
