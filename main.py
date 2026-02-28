
# ===== Imports =====
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters
from google import genai
import os

# ===== Environment Variables =====
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot, None, workers=0)  # Dispatcher for webhook updates

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
    prompt = (
        f"Write a short and fun poem (3-4 lines) describing the picture at this URL: {photo_url}. "
        "Make it creative, kid-friendly, and vivid. Only respond with the poem text."
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()

# ===== Telegram photo handler =====
def handle_photo(update: Update, context):
    if update.message.photo:
        # Take the largest version
        file_id = update.message.photo[-1].file_id
        file = bot.get_file(file_id)
        photo_url = file.file_path

        # Generate poem
        poem = generate_poem(photo_url)

        # Send reply
        update.message.reply_text(poem)

# Register handler
dp.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# ===== Run Flask app =====
if __name__ == "__main__":
    import threading

    def run_web():
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)

    threading.Thread(target=run_web).start()
