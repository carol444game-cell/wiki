import os
from telegram import Update, ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import wikipediaapi
from googletrans import Translator

# Bot token va portni olish
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8443))

# Wikipedia va Translator
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
wiki = wikipediaapi.Wikipedia('en', headers={'User-Agent': user_agent})
translator = Translator()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am a Wikipedia bot. Send me any topic and I will search it on Wikipedia!"
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    page = wiki.page(query)
    if page.exists():
        summary = page.summary[0:5000]
        user_lang = get_user_language(update)

        if user_lang != 'en':
            try:
                summary = translator.translate(summary, dest=user_lang).text
            except Exception as e:
                print(f"Translation error: {e}")

        await send_long_text(update, summary)
    else:
        await update.message.reply_text("No results found for that search.")


async def send_long_text(update: Update, text: str):
    chunks = [text[i:i + 3000] for i in range(0, len(text), 3000)]
    for chunk in chunks:
        await update.message.reply_text(chunk)


def get_user_language(update: Update):
    if update.message.from_user and update.message.from_user.language_code:
        return update.message.from_user.language_code.lower()
    return 'en'


if __name__ == "__main__":
    # Render yoki boshqa server domeni avtomatik aniqlanishi uchun
    DOMAIN = os.environ.get("RENDER_EXTERNAL_URL")  # Render serveri avtomatik beradi
    if not DOMAIN:
        raise ValueError("RENDER_EXTERNAL_URL environment variable is not set!")

    webhook_url = f"https://{DOMAIN}/{BOT_TOKEN}"

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
        webhook_url=webhook_url
    )
