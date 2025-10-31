# Komisec.py
import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask

# ========== CONFIG ==========
TOKEN = os.getenv("BOT_TOKEN")  # your bot token (set in Render)
FORBIDDEN_ROLE_IDS = [1430761119689211934, 1430761012138872973]  # IDs of roles that should NOT be banned
DRY_RUN = False  # set True to test without actually banning anyone
PORT = int(os.getenv("PORT", 10000))  # Render uses PORT env automatically
# ============================

# ====== DISCORD CLIENT SETUP ======
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
# =================================

# ====== FLASK SERVER (for Render) ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Komisec auto-ban bot is running.", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)
# ======================================


# ====== DISCORD LOGIC ======
@bot.event
async def on_ready():
    print(f"✅ Auto-ban bot ready as {bot.user} — connected to {len(bot.guilds)} guild(s).")

    for guild in bot.guilds:
        print(f"🔍 Scanning guild: {guild.name}")
        banned_count = 0

        for member in guild.members:
            if member.bot:
                continue  # skip bots

            has_forbidden_role = any(role.id in FORBIDDEN_ROLE_IDS for role in member.roles)
            if has_forbidden_role:
                print(f"⏭️ Skipping {member} (has protected role)")
                continue

            try:
                if not DRY_RUN:
                    await member.ban(reason="Auto-ban: Minor detected, exterminated with extreme prejudice")
                    print(f"❌ Banned {member}")
                else:
                    print(f"[DRY RUN] Would ban {member}")
                banned_count += 1
                await asyncio.sleep(1.5)  # avoid rate limits
            except Exception as e:
                print(f"⚠️ Could not ban {member}: {e}")

        print(f"✅ Finished scanning {guild.name}. Total banned: {banned_count}")

    print("🛑 Auto-ban cycle complete.")
# =======================================


# ====== STARTUP ======
if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask).start()  # keep Render alive

    if not TOKEN:
        print("❌ BOT_TOKEN not found in environment variables.")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Invalid Discord token. Please check BOT_TOKEN in Render.")
# ======================
