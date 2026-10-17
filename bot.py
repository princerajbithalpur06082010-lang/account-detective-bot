import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. Render Port Binding (Fixes Render Red Error) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

    def log_message(self, format, *args):
        return  # Keep logs clean

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- 2. Bot Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🔍 *ACCOUNT INSPECTOR & RECOVERY BOT*\n\n"
        "Kisi bhi account ka status check karne aur ban/restriction ka reason aur solution janne ke liye command bhejein:\n\n"
        "• `/insta <username>` — Instagram Account\n"
        "• `/tele <username>` — Telegram Account\n"
        "• `/fb <username>` — Facebook Profile\n"
        "• `/yt <channel_name>` — YouTube Channel\n\n"
        "_Example:_ `/insta username`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def insta_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please username provide karein.\nExample: `/insta zuck`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    await update.message.reply_text(f"🔍 Checking Instagram account @{username}...")

    profile_url = f"https://www.instagram.com/{username}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(profile_url, headers=headers, timeout=5)
        is_restricted = response.status_code == 404
    except Exception:
        is_restricted = True

    status_str = "⚠️ Not Reachable / Likely Suspended or Banned" if is_restricted else "✅ Publicly Available / Active"

    report = (
        f"📋 *INSTAGRAM INSPECTION REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• *Target Username:* `@{username}`\n"
        f"• *Current Status:* {status_str}\n\n"
        f"⚠️ *Probable Ban / Restriction Reasons:*\n"
        f"1. **Spam Activity:** Too many DMs, mass unfollow/follow, or repetitive comments.\n"
        f"2. **Third-party Apps:** Using unfollower-trackers or automated bots.\n"
        f"3. **Community Guidelines:** Copyright violation, adult content, or harassment reports.\n\n"
        f"🛠 *Official Recovery Solution:*\n"
        f"• **Step 1:** Instagram app open karein aur login karein. Agar 'Account Disabled' popup aaye to 'Learn More' par tap karein.\n"
        f"• **Step 2:** Official disabled appeal form bharein:\n"
        f"🔗 https://help.instagram.com/contact/606967319425038\n"
        f"• **Step 3:** Selfie verification code aane par clear photo bhejein."
    )
    await update.message.reply_text(report, parse_mode="Markdown")

async def tele_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please username provide karein.\nExample: `/tele username`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    report = (
        f"📋 *TELEGRAM INSPECTION REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"• *Username:* `@{username}`\n\n"
        f"⚠️ *Probable Ban / SpamLock Reasons:*\n"
        f"1. Unknown logo ko direct mass message karna.\n"
        f"2. Groups mein spam links ya automated messages share karna.\n"
        f"3. Multiple users dwara 'Report Spam' dabana.\n\n"
        f"🛠 *Official Recovery Solution:*\n"
        f"• Telegram par seedha **@SpamBot** open karein aur `/start` dabayein.\n"
        f"• Bot batayega restriction permanent hai ya temporary, aur wahan se appeal submit karein."
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# --- 3. Main Runner ---
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable not set!")

    # Start dummy web server in background for Render
    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()

    # Start Telegram Polling
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("insta", insta_check))
    app.add_handler(CommandHandler("tele", tele_check))

    print("Bot is up and polling...")
    app.run_polling()
    
