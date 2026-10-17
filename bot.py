import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

BOT_NAME = "Account Inspector"


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = (
        "🔎 ACCOUNT INSPECTOR\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome to Account Inspector.\n\n"
        "Analyze publicly available account information "
        "across supported social platforms.\n\n"
        "AVAILABLE COMMANDS\n"
        "/insta <username> — Instagram\n"
        "/tele <username> — Telegram\n"
        "/fb <username> — Facebook\n"
        "/yt <username> — YouTube\n\n"
        "Example: /insta username\n\n"
        "Note: Private moderation records are not publicly "
        "accessible. Restriction reasons are reported only "
        "when supported by reliable evidence."
    )
    await update.message.reply_text(message)


async def inspect_account(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    command = update.message.text.split()[0].split("@")[0]
    platform = {
        "/insta": "Instagram",
        "/tele": "Telegram",
        "/fb": "Facebook",
        "/yt": "YouTube",
    }.get(command, "Unknown")

    if not context.args:
        await update.message.reply_text(
            f"Usage: {command} <username>\n"
            f"Example: {command} username"
        )
        return

    username = " ".join(context.args).strip().lstrip("@")

    report = (
        "🔎 ACCOUNT INSPECTION REPORT\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Platform: {platform}\n"
        f"Username: @{username}\n\n"
        "ACCOUNT INFORMATION\n"
        "• Profile Details: Not yet retrieved\n"
        "• Account Status: Unverified\n\n"
        "SECURITY & RESTRICTIONS\n"
        "• Restriction Status: Unverified\n"
        "• Exact Reason: Not confirmed\n"
        "• Official Evidence: Not retrieved\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Data integration is not configured yet.\n"
        "No account status has been verified."
    )

    await update.message.reply_text(report)


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(
        ["insta", "tele", "fb", "yt"],
        inspect_account
    ))

    logger.info("%s is starting...", BOT_NAME)
    app.run_polling()


if __name__ == "__main__":
    main()
