# bot.py
# Simple auto-ban bot (discord.py v2)
# Edit the CONFIG section below with your role IDs and channel ID.

import os
import asyncio
import discord
from discord.ext import commands
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# -------------------- CONFIG (EDIT THESE) --------------------
FORBIDDEN_ROLE_IDS = [
    1430761012138872973,  # example: replace with actual role IDs
    1430761119689211934
]

LOG_CHANNEL_ID = 1399460846379466782  # replace with your channel ID

CUSTOM_MESSAGE = "Banned {user} (ID: {user_id}) had role {role}"

DRY_RUN = False
# ------------------------------------------------------------

intents = discord.Intents.default()
intents.members = True  # REQUIRED: enable "Server Members Intent"
bot = commands.Bot(command_prefix="!", intents=intents)

async def send_log(guild: discord.Guild, content: str):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        try:
            await ch.send(content)
        except Exception as e:
            print(f"[{guild.name}] Failed to send log message: {e}\nContent: {content}")
    else:
        print(f"[{guild.name}] LOG CHANNEL NOT FOUND. Would send: {content}")

async def try_ban_member(member: discord.Member, detected_role: discord.Role):
    guild = member.guild
    if member == guild.owner:
        await send_log(guild, f"Skipped banning server owner: {member} ({member.id})")
        return False
    if not any(r.id in FORBIDDEN_ROLE_IDS for r in member.roles):
        return False
    if DRY_RUN:
        msg = CUSTOM_MESSAGE.format(user=member.mention, user_id=member.id, guild=guild.name, role=detected_role.name)
        await send_log(guild, "(dry-run) " + msg)
        print(f"(dry-run) Would ban {member} ({member.id}) for role {detected_role.name} in {guild.name}")
        return True
    me = guild.me
    if me is None:
        await send_log(guild, f"Bot member object missing; can't ban {member}.")
        return False
    if member.top_role >= me.top_role:
        await send_log(guild, f"Cannot ban {member} ({member.id}) because their top role >= bot's top role.")
        return False
    try:
        await guild.ban(member, reason=f"Auto-ban: Minor detected, exterminated with extreme prejudice {detected_role.name} ({detected_role.id})")
        msg = CUSTOM_MESSAGE.format(user=member.mention, user_id=member.id, guild=guild.name, role=detected_role.name)
        await send_log(guild, msg)
        print(f"Banned {member} ({member.id}) for role {detected_role.name} in {guild.name}")
        return True
    except Exception as e:
        await send_log(guild, f"Failed to ban {member} ({member.id}): {e}")
        print(f"Failed to ban {member} ({member.id}): {e}")
        return False

@bot.event
async def on_ready():
    print(f"Auto-ban bot ready as {bot.user} — connected to {len(bot.guilds)} guild(s).")
    if DRY_RUN:
        print("DRY_RUN is ON — bot will not actually perform bans. Set DRY_RUN = False to enable banning.")

@bot.event
async def on_member_join(member: discord.Member):
    for r in member.roles:
        if r.id in FORBIDDEN_ROLE_IDS:
            await try_ban_member(member, r)
            break

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    added = after_ids - before_ids
    if not added:
        return
    for role_id in added:
        if role_id in FORBIDDEN_ROLE_IDS:
            role_obj = after.guild.get_role(role_id)
            await try_ban_member(after, role_obj or discord.Object(id=role_id))
            return

@bot.command()
@commands.is_owner()
async def show_config(ctx):
    await ctx.send(
        f"FORBIDDEN_ROLE_IDS: {FORBIDDEN_ROLE_IDS}\n"
        f"LOG_CHANNEL_ID: {LOG_CHANNEL_ID}\n"
        f"DRY_RUN: {DRY_RUN}"
    )

# -------------------- Render HTTP server --------------------
PORT = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    server = HTTPServer(("", PORT), Handler)
    print(f"HTTP server running on port {PORT}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# -------------------- Start the bot --------------------
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERROR: please set BOT_TOKEN environment variable.")
        raise SystemExit(1)
    bot.run(token)
