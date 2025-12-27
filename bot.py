import os
# eski: from telegram import Update, ChatAction
from telegram import Update
from telegram.constants import ChatAction

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import wikipediaapi
from deep_translator import GoogleTranslator

# Bot token va portni olish
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8443))

# Render domeni avtomatik aniqlash
DOMAIN = os.environ.get("RENDER_EXTERNAL_URL")
if not DOMAIN:
    raise ValueError("RENDER_EXTERNAL_URL environment variable is not set!")

WEBHOOK_URL = f"https://{DOMAIN}/{BOT_TOKEN}"

# Wikipedia va Translator
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
wiki = wikipediaapi.Wikipedia('en', headers={'User-Agent': user_agent})


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    welcome_message = (
        "👋 Hello! I am your Wikipedia bot.\n\n"
        "Send me any topic and I will search it on Wikipedia.\n"
        "I can also translate the summary into your language automatically."
    )
    await update.message.reply_text(welcome_message)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi yozgan matnni Wikipedia'dan qidiradi"""
    query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    page = wiki.page(query)
    if page.exists():
        summary = page.summary[0:5000]
        user_lang = get_user_language(update)

        # Foydalanuvchi tili inglizcha bo'lmasa, tarjima qilamiz
        if user_lang != 'en':
            try:
                summary = GoogleTranslator(source='en', target=user_lang).translate(summary)
            except Exception as e:
                print(f"Translation error: {e}")

        await send_long_text(update, summary)
    else:
        await update.message.reply_text("No results found for that search.")


async def send_long_text(update: Update, text: str):
    """Uzun matnni 3000 belgi bo‘lib yuboradi"""
    chunks = [text[i:i + 3000] for i in range(0, len(text), 3000)]
    for chunk in chunks:
        await update.message.reply_text(chunk)


def get_user_language(update: Update):
    """Foydalanuvchi tilini aniqlaydi"""
    if update.message.from_user and update.message.from_user.language_code:
        return update.message.from_user.language_code.lower()
    return 'en'


if __name__ == "__main__":
    # Botni qurish
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    # Webhook sozlash
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )

