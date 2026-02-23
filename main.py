import os
import aiohttp
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
import uvicorn

# Environment variables (Render pe Secrets mein set karna)
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "nullprotocol-bot")  # change kar sakte ho
API_URL = "https://tg2num-owner-api.vercel.app/?userid="

app = FastAPI()
application = None

# ────────────────────────────────────────────────
# Inline Keyboards
# ────────────────────────────────────────────────

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔍 ID Check Karo", callback_data="search")],
        [InlineKeyboardButton("❓ Help Chahiye?", callback_data="help")],
        [InlineKeyboardButton("👨‍💻 Developer se Baat", url="https://t.me/Nullprotocol_X")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_after_search_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔄 Aur Ek Check Karo", callback_data="search")],
        [InlineKeyboardButton("🏠 Main Menu Pe Wapas", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ────────────────────────────────────────────────
# Command Handlers
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey bhai! 👋\n\n"
        "Main tera Telegram User ID Checker Bot hoon 🔥\n"
        "Kisi bhi Telegram ID se details nikaal sakta hoon (country, code, number etc.)\n\n"
        "Bas User ID bhej do (jaise 123456789) ya neeche buttons se start karo!",
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Help section bhai:\n\n"
        "• Direct User ID type kar do (sirf numbers, example: 123456789)\n"
        "• Ya /search <ID> use kar sakte ho\n"
        "• Result mein sirf important info dikhegi\n\n"
        "Yeh third-party API use karta hai, so careful rehna\n"
        "Koi issue ho to Developer ko ping kar dena!",
        reply_markup=get_main_menu_keyboard()
    )


# ────────────────────────────────────────────────
# Inline Button Callback
# ────────────────────────────────────────────────

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        await query.message.reply_text(
            "Bhai ab User ID bhej do (example: 123456789) 😎"
        )
    elif query.data == "help":
        await help_command(update, context)
    elif query.data == "main_menu":
        await query.message.edit_text(
            "Hey bhai! 👋\n\n"
            "Main tera Telegram User ID Checker Bot hoon 🔥\n"
            "Kisi bhi Telegram ID se details nikaal sakta hoon\n\n"
            "Bas User ID bhej do ya buttons use karo!",
            reply_markup=get_main_menu_keyboard()
        )


# ────────────────────────────────────────────────
# Main Search Logic
# ────────────────────────────────────────────────

async def search_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Command se args ya direct text se userid le lo
    if context.args:
        userid = context.args[0].strip()
    else:
        userid = update.message.text.strip()

    if not userid.isdigit():
        await update.message.reply_text(
            "❌ Galat input bhai!\nSirf numbers daalo (jaise 123456789)"
        )
        return

    # Searching message bhej ke edit karenge baad mein
    searching_msg = await update.message.reply_text(
        f"🔍 User ID {userid} check kar raha hoon... Ruk ja 2 sec!"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL + userid, timeout=12) as resp:
                data = await resp.json()

                found = False
                message_text = "Kuch nahi mila"
                country = "N/A"
                country_code = "N/A"
                number = "N/A"

                # API response handle karo (dono formats)
                if isinstance(data, dict):
                    status = data.get("status", "").lower()

                    if status in ["success", "ok"]:
                        inner = data.get("data", {})
                        found = inner.get("found", False)
                        message_text = inner.get("message", "Details fetched" if found else "Phone number not found")
                        if found:
                            country = inner.get("country", "N/A")
                            country_code = inner.get("country_code", "N/A")
                            number = inner.get("number", "N/A")

                    elif status == "not_found" or data.get("code") == 404:
                        inner = data.get("data", {})
                        found = inner.get("found", False)
                        message_text = inner.get("message", "Phone number not found")

                    else:
                        message_text = data.get("message", "Unexpected response from API")

                # Final clean message
                response_text = f"{'✅' if found else '❌'} {'Mil gaya bhai!' if found else 'Sorry bhai, kuch nahi mila'}\n\n"
                response_text += f"Message: {message_text}\n"

                if found:
                    response_text += f"Country: {country}\n"
                    response_text += f"Country Code: {country_code}\n"
                    response_text += f"Phone Number: {number}\n"

                response_text += "\nDeveloper: @Nullprotocol_X\nPowered by: NULL PROTOCOL"

                await searching_msg.edit_text(
                    response_text,
                    reply_markup=get_after_search_keyboard()
                )

        except Exception as e:
            error_text = (
                f"⚠️ Oops! Kuch gadbad ho gayi\n"
                f"Error: {str(e)}\n"
                "Thodi der baad phir try karna bhai"
            )
            error_text += "\n\nDeveloper: @Nullprotocol_X\nPowered by: NULL PROTOCOL"

            await searching_msg.edit_text(
                error_text,
                reply_markup=get_after_search_keyboard()
            )


# ────────────────────────────────────────────────
# FastAPI Webhook Setup
# ────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    global application
    application = Application.builder().token(TOKEN).build()

    # Handlers add karo
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_userid))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_userid))

    # Webhook set Telegram pe
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{WEBHOOK_SECRET}"
    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    print(f"Webhook set ho gaya: {webhook_url}")


@app.post(f"/{WEBHOOK_SECRET}")
async def webhook(request: Request):
    if application is None:
        raise HTTPException(status_code=503, detail="Bot not ready")

    update_dict = await request.json()
    update = Update.de_json(update_dict, application.bot)

    if update:
        await application.process_update(update)
        return {"ok": True}

    raise HTTPException(status_code=400, detail="Invalid update")


@app.get("/")
async def root():
    return {"status": "NULL PROTOCOL Bot is live! 🚀"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
