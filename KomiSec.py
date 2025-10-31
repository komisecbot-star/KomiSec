# Komisec.py
import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask

# ========== CONFIG ==========
TOKEN = os.getenv("BOT_TOKEN")  # your bot token (set in Render)

# 🔥 Roles that SHOULD BE BANNED
BAN_ROLE_IDS = [1430761119689211934, 1430761012138872973]

DRY_RUN = False  # set True for testing without banning
PORT = int(os.getenv("PORT", 10000))
# ============================

# ====== DISCORD CLIENT SETUP ======
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
# =================================

# ====== FLASK KEEPALIVE (for Render) ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Komisec auto-ban bot is running.", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)
# ==========================================


# ====== MAIN DISCORD LOGIC ======
async def check_and_ban_member(member: discord.Member):
    """Check a single member and ban if they have a forbidden role."""
    # Skip bots
    if member.bot:
        return

    # Skip if role hierarchy prevents it
    if member.top_role >= member.guild.me.top_role:
        print(f"🚫 Cannot ban {member} — higher or equal role to bot.")
        return

    # Check if the member has any banned role
    if any(role.id in BAN_ROLE_IDS for role in member.roles):
        try:
            if not DRY_RUN:
                await member.ban(reason="Auto-ban: Minor detected, exterminated with extreme prejudice")
                print(f"✅ Banned {member}")
            else:
                print(f"[DRY RUN] Would ban {member}")
            await asyncio.sleep(1.5)  # avoid rate limits
        except discord.Forbidden:
            print(f"⚠️ Missing permissions to ban {member}")
        except discord.HTTPException as e:
            print(f"❌ HTTP error while banning {member}: {e}")
    else:
        # No banned roles, safe
        return


@bot.event
async def on_ready():
    print(f"✅ Komisec ready as {bot.user} — connected to {len(bot.guilds)} guild(s).")

    for guild in bot.guilds:
        print(f"🔍 Scanning guild: {guild.name}")
        banned_count = 0

        for member in guild.members:
            before = banned_count
            await check_and_ban_member(member)
            if before != banned_count:
                banned_count += 1

        print(f"✅ Finished scanning {guild.name}. Total banned: {banned_count}")

    print("🛑 Initial auto-ban cycle complete.")


@bot.event
async def on_member_join(member):
    """Check and ban users automatically when they join."""
    print(f"👋 {member} joined {member.guild.name}, checking roles...")
    await asyncio.sleep(2)  # short delay to let roles apply
    await check_and_ban_member(member)
# ===========================================


# ====== STARTUP ======
if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask).start()

    if not TOKEN:
        print("❌ BOT_TOKEN not found in environment variables.")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Invalid Discord token. Please check BOT_TOKEN in Render.")
# ======================
