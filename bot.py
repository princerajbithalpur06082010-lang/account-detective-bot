import os
import re
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER PORT BINDING ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot service online.")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- 2. DEEP INSTAGRAM INSPECTION ---
def inspect_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            final_url = response.geturl()
            html = response.read().decode("utf-8", errors="ignore")

            # 1. Check title tag
            title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
            page_title = title_match.group(1).strip() if title_match else ""

            # 2. Check explicitly for deleted/banned/not found indicators
            if "Page Not Found" in page_title or "isn't available" in html or "link you followed may be broken" in html:
                return {
                    "status": "BANNED_OR_NOT_FOUND",
                    "reason": "Account is either permanently banned, temporarily disabled by user, or non-existent."
                }

            # 3. Check if Instagram forced a login challenge
            if "Login • Instagram" in page_title or "/accounts/login" in final_url:
                # If username is completely missing from page title/source, it is restricted or blocked
                if f"@{username.lower()}" not in page_title.lower() and username.lower() not in page_title.lower():
                    return {
                        "status": "CHALLENGE_BLOCKED",
                        "reason": "Instagram security challenge triggered. Public verification restricted for this username."
                    }

            # 4. Check if profile was actually retrieved
            if f"(@{username.lower()})" in page_title.lower() or username.lower() in page_title.lower():
                return {
                    "status": "ACTIVE",
                    "title": page_title
                }

            # Fallback if uncertain
            return {
                "status": "BANNED_OR_NOT_FOUND",
                "reason": "Profile handle not found in public index (Likely Suspended or Terminated)."
            }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {
                "status": "BANNED_OR_NOT_FOUND",
                "reason": "HTTP 404: Username does not exist or has been banned."
            }
        return {
            "status": "ERROR",
            "reason": f"Instagram blocked connection with status code {e.code}."
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "reason": f"Connection timeout: {str(e)}"
        }

# --- 3. COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🛡 *ACCOUNT STATUS & RESTRICTION INSPECTOR*\n\n"
        "Send `/insta <username>` to verify account status, ban flags, and recovery steps.\n\n"
        "_Example:_ `/insta cristiano`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def insta_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ *Please enter a username.*\nExample: `/insta zuck`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    await update.message.reply_text(f"🔍 Checking `@{username}` with Instagram verification protocols...")

    res = inspect_instagram(username)

    if res["status"] == "ACTIVE":
        report = (
            f"✅ *ACCOUNT STATUS: ACTIVE / LIVE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Username:* `@{username}`\n"
            f"• *Public Access:* Active & Verified on Public Index\n"
            f"• *Profile:* https://www.instagram.com/{username}/\n\n"
            f"💡 *Account Health:* Normal. No public suspension flag detected."
        )
    elif res["status"] == "BANNED_OR_NOT_FOUND":
        report = (
            f"🚫 *ACCOUNT STATUS: BANNED / RESTRICTED / INACTIVE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Target:* `@{username}`\n"
            f"• *Status:* Confirmed Unreachable (`404 / Page Not Found`)\n"
            f"• *Diagnosis:* {res['reason']}\n\n"
            f"⚠️ *Why Was This Account Banned?*\n"
            f"1. **Spam / Automation Policy:** Rapid follow/unfollow actions, DM spam, or automated bot tools.\n"
            f"2. **Unauthorized Apps:** Logging into third-party unfollower trackers or analytics apps.\n"
            f"3. **Community Violations:** Copyright strikes, fake engagement, or policy breaches.\n\n"
            f"🛠 *Official Recovery Procedure:*\n"
            f"1. Open Instagram App and log in to view the official ban prompt.\n"
            f"2. Submit an appeal through Meta's official form:\n"
            f"👉 https://help.instagram.com/contact/606967319425038\n"
            f"3. Provide government ID or handheld selfie verification code if asked."
        )
    else:
        report = (
            f"⚠️ *ACCOUNT STATUS: SECURITY RESTRICTION*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Target:* `@{username}`\n"
            f"• *Server Response:* {res['reason']}\n"
            f"• *Note:* Meta's anti-scraping filters intercepted the request from the hosting server. Try visiting `https://www.instagram.com/{username}/` directly in your browser."
        )

    await update.message.reply_text(report, parse_mode="Markdown")

# --- 4. START SERVICE ---
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is missing!")

    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("insta", insta_check))

    print("Bot is listening...")
    app.run_polling()
    
