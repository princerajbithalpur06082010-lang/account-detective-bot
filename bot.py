import os
import json
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER PORT BINDING (Fixes Port Scan Timeout) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- 2. DATA SCRAPING FUNCTION ---
def get_instagram_data(username):
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15",
        "x-ig-app-id": "936619743392459"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode())
            user = data.get("data", {}).get("user")
            if user:
                return {
                    "exists": True,
                    "followers": user.get("edge_followed_by", {}).get("count", 0),
                    "following": user.get("edge_follow", {}).get("count", 0),
                    "posts": user.get("edge_owner_to_timeline_media", {}).get("count", 0),
                    "bio": user.get("biography", "No Bio").strip(),
                    "is_private": user.get("is_private", False)
                }
    except Exception:
        pass
    return {"exists": False}

# --- 3. BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🔍 *ALL-IN-ONE SOCIAL DETECTIVE BOT*\n\n"
        "Kisi bhi account ki details, ban status aur unban solution dekhne ke liye command dein:\n\n"
        "📸 `/insta <username>` — Instagram (Followers, Posts, Ban/Recovery)\n"
        "✈️ `/tele <username>` — Telegram Restrictions & Fix\n"
        "👤 `/fb <username>` — Facebook Status & Appeal\n"
        "🎥 `/yt <channel>` — YouTube Guidelines & Recovery\n\n"
        "_Example:_ `/insta cristiano`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def insta_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please username likhein.\nExample: `/insta cristiano`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    await update.message.reply_text(f"🔎 Scanning `@{username}` across Instagram servers...")

    info = get_instagram_data(username)

    if info["exists"]:
        privacy = "🔒 Private Account" if info["is_private"] else "🔓 Public Account"
        bio_clean = info["bio"].replace("_", "\\_").replace("*", "\\*")[:150]
        report = (
            f"✅ *ACCOUNT FOUND & ACTIVE*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Username:* `@{username}`\n"
            f"🔐 *Type:* {privacy}\n"
            f"👥 *Followers:* `{info['followers']:,}`\n"
            f"👤 *Following:* `{info['following']:,}`\n"
            f"📸 *Total Posts/Reels:* `{info['posts']:,}`\n"
            f"📝 *Bio:* {bio_clean}\n\n"
            f"🟢 *Status:* Healthy & Not Banned\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *Safe Practice:* Unfollow apps ya bulk DMs use na karein taaki shadowban na lage."
        )
    else:
        report = (
            f"⚠️ *ACCOUNT NOT FOUND / BANNED*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Target: `@{username}`\n"
            f"Status: **Suspended, Disabled ya Username Changed**\n\n"
            f"🛑 *Kyun Ban/Restrict Hoti Hai ID?*\n"
            f"1. **Follower/Unfollower Trackers:** 3rd party apps mein login karne par automated activity detect hona.\n"
            f"2. **Spam & Fast Actions:** Ek ghante mein bohot saare logo ko follow/unfollow karna ya DMs bhejna.\n"
            f"3. **Community Reports:** Copyright music, misleading claims, ya adult content ki strike aana.\n\n"
            f"🛠 *Kaise Theek Hoga? (Official Solution):*\n"
            f"• **Step 1:** Official Instagram Disabled Appeal form open karein:\n"
            f"👉 https://help.instagram.com/contact/606967319425038\n"
            f"• **Step 2:** Apna Full Name, Email aur Instagram Username submit karein.\n"
            f"• **Step 3:** Meta se email aane par code ko kagaz par haath se likhkar selfie ke sath reply karein."
        )

    await update.message.reply_text(report, parse_mode="Markdown")

async def tele_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please username likhein.\nExample: `/tele username`", parse_mode="Markdown")
        return

    username = context.args[0].replace("@", "").strip()
    report = (
        f"✈️ *TELEGRAM INSPECTION: @{username}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛑 *SpamLock / Ban Hone Ke Kaaran:*\n"
        f"1. Aise logo ko DM karna jinke paas aapka number save nahi hai.\n"
        f"2. Multiple users ka 'Report as Spam' dabana.\n"
        f"3. Public groups mein referral ya crypto spam links drop karna.\n\n"
        f"🛠 *Solution & Unban Process:*\n"
        f"• Telegram par **@SpamBot** kholein aur `/start` bhejein.\n"
        f"• Agar temporary limit hai to exact date pata chal jayegi.\n"
        f"• 'This is a mistake' select karke official appeal submit karein."
    )
    await update.message.reply_text(report, parse_mode="Markdown")

# --- 4. MAIN APPLICATION ---
if __name__ == "__main__":
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN variable missing!")

    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("insta", insta_check))
    app.add_handler(CommandHandler("tele", tele_check))

    print("Bot is up and running...")
    app.run_polling()
            
