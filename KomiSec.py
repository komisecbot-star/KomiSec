import os
import asyncio
import discord
from discord.ext import commands
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# -------------------- CONFIG --------------------
FORBIDDEN_ROLE_IDS = [
    1430761012138872973,  # example: replace with actual role IDs
    1430761119689211934
]

LOG_CHANNEL_ID = 1399460846379466782  # replace with your log channel ID
CUSTOM_MESSAGE = "Banned {user} (ID: {user_id}) had role {role}"
DRY_RUN = False
# ------------------------------------------------

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------- Logging --------------------
async def send_log(guild: discord.Guild, content: str):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        try:
            await ch.send(content)
        except Exception as e:
            print(f"[{guild.name}] Failed to send log message: {e}\nContent: {content}")
    else:
        print(f"[{guild.name}] LOG CHANNEL NOT FOUND. Would send: {content}")


# -------------------- Ban logic --------------------
async def try_ban_member(member: discord.Member, detected_role: discord.Role):
    guild = member.guild

    if member == guild.owner:
        await send_log(guild, f"Skipped banning server owner: {member} ({member.id})")
        return False

    if not any(r.id in FORBIDDEN_ROLE_IDS for r in member.roles):
        return False

    me = guild.me
    if me is None:
        await send_log(guild, f"Bot member object missing; can't ban {member}.")
        return False

    if member.top_role >= me.top_role:
        await send_log(guild, f"Cannot ban {member} ({member.id}) because their top role >= bot's top role.")
        return False

    msg = CUSTOM_MESSAGE.format(user=member.mention, user_id=member.id, role=detected_role.name)

    if DRY_RUN:
        await send_log(guild, "(dry-run) " + msg)
        print(f"(dry-run) Would ban {member} ({member.id}) for role {detected_role.name} in {guild.name}")
        return True

    try:
        await guild.ban(
            member,
            reason=f"Auto-ban: Minor detected, exterminated with extreme prejudice {detected_role.name} ({detected_role.id})"
        )
        await send_log(guild, msg)
        print(f"Banned {member} ({member.id}) for role {detected_role.name} in {guild.name}")
        return True
    except Exception as e:
        await send_log(guild, f"Failed to ban {member} ({member.id}): {e}")
        print(f"Failed to ban {member} ({member.id}): {e}")
        return False


# -------------------- Event handlers --------------------
@bot.event
async def on_ready():
    print(f"✅ Auto-ban bot ready as {bot.user} — connected to {len(bot.guilds)} guild(s).")

    if DRY_RUN:
        print("⚠️ DRY_RUN is ON — bot will not actually perform bans.")

    # Scan all existing members (catch anyone who joined while bot was offline)
    print("🔍 Checking existing members for forbidden roles...")
    for guild in bot.guilds:
        for member in guild.members:
            for role in member.roles:
                if role.id in FORBIDDEN_ROLE_IDS:
                    await try_ban_member(member, role)
                    break
    print("✅ Initial scan complete.")


@bot.event
async def on_member_join(member: discord.Member):
    print(f"👋 Member joined: {member} ({member.id}) in {member.guild.name}")
    # Check if they already have a forbidden role (can happen with bots)
    for role in member.roles:
        if role.id in FORBIDDEN_ROLE_IDS:
            await try_ban_member(member, role)
            break


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    added_roles = after_ids - before_ids

    if not added_roles:
        return

    for role_id in added_roles:
        if role_id in FORBIDDEN_ROLE_IDS:
            role_obj = after.guild.get_role(role_id)
            print(f"⚠️ Detected forbidden role added: {role_obj.name if role_obj else role_id} to {after}")
            await try_ban_member(after, role_obj or discord.Object(id=role_id))
            break


# -------------------- Owner command --------------------
@bot.command()
@commands.is_owner()
async def show_config(ctx):
    await ctx.send(
        f"FORBIDDEN_ROLE_IDS: {FORBIDDEN_ROLE_IDS}\n"
        f"LOG_CHANNEL_ID: {LOG_CHANNEL_ID}\n"
        f"DRY_RUN: {DRY_RUN}"
    )


# -------------------- Render HTTP Server --------------------
PORT = int(os.environ.get("PORT", 10000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()  # Prevents 501 spam in logs

def run_server():
    server = HTTPServer(("", PORT), Handler)
    print(f"🌐 HTTP server running on port {PORT}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()


# -------------------- Start the bot --------------------
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ ERROR: please set BOT_TOKEN environment variable.")
        raise SystemExit(1)
    bot.run(token)
