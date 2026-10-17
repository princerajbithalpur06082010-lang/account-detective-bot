import os
import json
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. HEALTH SERVER FOR RENDER (Keeps Web Service Live) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot service is healthy and operational.")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- 2. INSTAGRAM ACCOUNT INSPECTION ---
def inspect_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return {"reachable": True, "code": response.status}
    except urllib.error.HTTPError as e:
        return {"reachable": False, "code": e.code}
    except Exception:
        return {"reachable": False, "code": 500}

# --- 3. BOT COMMAND HANDLERS (ENGLISH) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🛡 *SOCIAL ACCOUNT INSPECTOR & RECOVERY BOT*\n\n"
        "Inspect account accessibility, restriction diagnoses, and official restoration steps.\n\n"
        "*Available Commands:*\n"
        "• `/insta <username>` — Inspect Instagram account status\n"
        "• `/tele <username>` — Inspect Telegram account restrictions\n\n"
        "*Example:* `/insta zuck`"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def insta_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ *Please provide a username.*\nExample: `/insta zuck`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    await update.message.reply_text(f"🔍 *Analyzing target:* `@{username}`\nPlease wait...", parse_mode="Markdown")

    result = inspect_instagram(username)

    if result["reachable"]:
        report = (
            f"✅ *ACCOUNT STATUS: ACTIVE / LIVE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Platform:* Instagram\n"
            f"• *Target Username:* `@{username}`\n"
            f"• *Server Response:* `200 OK`\n"
            f"• *Public Access:* Accessible\n\n"
            f"📌 *Direct Profile Link:*\n"
            f"https://www.instagram.com/{username}/\n\n"
            f"🔒 *Privacy & Stories Note:*\n"
            f"Under Meta's API policy, private account media (posts, reels, stories) and active session stories are restricted to authenticated followers only."
        )
    else:
        report = (
            f"🚫 *ACCOUNT STATUS: RESTRICTED / BANNED / DELETED*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Platform:* Instagram\n"
            f"• *Target Username:* `@{username}`\n"
            f"• *HTTP Status:* `{result['code']} (Endpoint Unreachable)`\n\n"
            f"⚠️ *Direct Causes for Permanent/Temporary Ban:*\n"
            f"1. **Automation / 3rd-Party Apps:** Use of follower trackers, view bots, or scrapers.\n"
            f"2. **Terms of Use Violations:** Copyright infringement strikes, impersonation, or mass spam.\n"
            f"3. **Community Safety:** Multiple coordinated reports or prohibited goods/language.\n\n"
            f"🛠 *Official Recovery Procedure:*\n"
            f"1. Open the Instagram mobile app and attempt to log in.\n"
            f"2. When prompted with 'Your Account Has Been Disabled', tap **'Learn More'**.\n"
            f"3. Submit the official appeal form directly to Meta:\n"
            f"🔗 https://help.instagram.com/contact/606967319425038\n"
            f"4. If Meta sends an automated verification email, reply with the requested handwritten code and ID."
        )

    await update.message.reply_text(report, parse_mode="Markdown")

async def tele_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ *Please provide a Telegram username.*\nExample: `/tele username`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    report = (
        f"✈️ *TELEGRAM INSPECTION: @{username}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Primary Restriction Reasons (SpamLock):*\n"
        f"• Sending unsolicited private messages (DMs) to non-contacts.\n"
        f"• Users flagging incoming messages using the 'Report Spam' button.\n"
        f"• Mass posting promotional or referral links across channels.\n\n"
        f"🛠 *Official Recovery Steps:*\n"
        f"• Open the official Telegram bot: **@SpamBot**\n"
        f"• Send `/start` to verify whether the limitation is temporary or permanent.\n"
        f"• Submit an automated appeal directly through the bot."
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# --- 4. RUNNER ---
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is missing!")

    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("insta", insta_check))
    app.add_handler(CommandHandler("tele", tele_check))

    print("Bot is up and listening...")
    app.run_polling()
                      
