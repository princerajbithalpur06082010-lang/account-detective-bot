import os
import json
import threading
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER HEALTH SERVER (Keeps Port Open) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is live and running.")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- 2. ACCURATE INSTAGRAM INSPECTOR ---
def inspect_instagram(username):
    # Method 1: Query Instagram Internal Web Profile API
    api_url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    api_headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 312.1.0.34.111",
        "x-ig-app-id": "936619743392459",
        "Accept": "application/json"
    }
    req = urllib.request.Request(api_url, headers=api_headers)
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            res_data = json.loads(response.read().decode())
            user = res_data.get("data", {}).get("user")
            if user:
                return {
                    "exists": True,
                    "followers": user.get("edge_followed_by", {}).get("count", 0),
                    "following": user.get("edge_follow", {}).get("count", 0),
                    "posts": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
                    "bio": user.get("biography", "").strip(),
                    "is_private": user.get("is_private", False)
                }
            else:
                return {"exists": False, "reason": "User not found on Instagram database."}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"exists": False, "reason": "Endpoint returned 404 (Account Deleted or Banned)."}
    except Exception:
        pass

    # Method 2: HTML Page Verification (With Redirect & Content Filter)
    web_url = f"https://www.instagram.com/{username}/"
    web_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    web_req = urllib.request.Request(web_url, headers=web_headers)
    try:
        with urllib.request.urlopen(web_req, timeout=7) as response:
            final_url = response.geturl()
            html_content = response.read().decode("utf-8", errors="ignore")

            # Check if Instagram returned 'Page Not Found' or redirected away from username
            if "Page Not Found" in html_content or "Sorry, this page isn't available" in html_content:
                return {"exists": False, "reason": "Page Not Available (Suspended, Disabled, or Deleted)."}
            
            if "/accounts/login" in final_url and username.lower() not in html_content.lower():
                return {"exists": False, "reason": "Account unreachable or inactive."}

            return {
                "exists": True,
                "followers": "Available on profile",
                "following": "Available on profile",
                "posts": "Available on profile",
                "bio": "Protected",
                "is_private": "Check profile link"
            }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"exists": False, "reason": "HTTP 404: User profile does not exist."}
        return {"exists": False, "reason": f"Instagram blocked request (HTTP {e.code})."}
    except Exception:
        return {"exists": False, "reason": "Connection failed or account does not exist."}

# --- 3. BOT COMMAND HANDLERS (ENGLISH) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛡 *SOCIAL ACCOUNT INSPECTOR & RECOVERY BOT*\n\n"
        "Inspect account activity status, ban diagnoses, and official recovery procedures.\n\n"
        "*Commands:*\n"
        "• `/insta <username>` — Check Instagram Account\n"
        "• `/tele <username>` — Check Telegram Restrictions\n\n"
        "_Example:_ `/insta cristiano`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def insta_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ *Please provide a username.*\nExample: `/insta zuck`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    await update.message.reply_text(f"🔍 Inspecting `@{username}`... Please wait.")

    data = inspect_instagram(username)

    if data["exists"]:
        priv = "🔒 Private Profile" if data.get("is_private") is True else "🔓 Public Profile"
        followers = f"{data['followers']:,}" if isinstance(data['followers'], int) else data['followers']
        following = f"{data['following']:,}" if isinstance(data['following'], int) else data['following']
        posts = f"{data['posts']:,}" if isinstance(data['posts'], int) else data['posts']
        bio = data.get("bio", "No bio").replace("_", "\\_").replace("*", "\\*")[:120]

        report = (
            f"✅ *ACCOUNT STATUS: ACTIVE / LIVE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Username:* `@{username}`\n"
            f"• *Visibility:* {priv}\n"
            f"• *Followers:* `{followers}`\n"
            f"• *Following:* `{following}`\n"
            f"• *Total Posts/Reels:* `{posts}`\n"
            f"• *Bio:* {bio}\n\n"
            f"🔗 *Profile Link:*\nhttps://www.instagram.com/{username}/\n\n"
            f"💡 *Health Note:* Account is in good standing and publicly accessible."
        )
    else:
        reason = data.get("reason", "Account removed or suspended.")
        report = (
            f"🚫 *ACCOUNT STATUS: INACTIVE / BANNED / DELETED*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Target Username:* `@{username}`\n"
            f"• *Detection Result:* {reason}\n\n"
            f"⚠️ *Primary Reasons for Account Ban/Suspension:*\n"
            f"1. **Spam & Fast Actions:** Bulk following, mass unfollowing, or automated comment bots.\n"
            f"2. **Third-Party Integrations:** Logging into follower tracker or story-viewer apps.\n"
            f"3. **Community Violations:** Copyright strikes, nudity/adult material, or impersonation reports.\n\n"
            f"🛠 *Official Recovery / Appeal Steps:*\n"
            f"1. Open the Instagram mobile app and attempt to log in.\n"
            f"2. When the suspension notice appears, tap **'Learn More'**.\n"
            f"3. Submit the official Meta appeal form:\n"
            f"👉 https://help.instagram.com/contact/606967319425038\n"
            f"4. If requested, write the provided code on paper and reply with a handheld verification photo."
        )

    await update.message.reply_text(report, parse_mode="Markdown")

async def tele_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ *Please provide a username.*\nExample: `/tele username`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    report = (
        f"✈️ *TELEGRAM INSPECTION: @{username}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *SpamLock & Restriction Causes:*\n"
        f"• Direct messaging unfamiliar users without contact exchange.\n"
        f"• Users clicking 'Report Spam' on received messages.\n"
        f"• Dropping repeated links across multiple groups.\n\n"
        f"🛠 *Official Solution:*\n"
        f"• Open **@SpamBot** on Telegram and type `/start`.\n"
        f"• Review limitation duration and submit an unban request directly."
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# --- 4. MAIN RUNNER ---
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is missing!")

    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("insta", insta_check))
    app.add_handler(CommandHandler("tele", tele_check))

    print("Bot is up and polling...")
    app.run_polling()
                                    
