# bot.py
# Simple auto-ban bot (discord.py v2)
# Edit the CONFIG section below with your role IDs and channel ID.

import os
import asyncio
import discord
from discord.ext import commands

# -------------------- CONFIG (EDIT THESE) --------------------
# Put the numeric role IDs you want automatically banned here:
FORBIDDEN_ROLE_IDS = [
    1430761012138872973,  # example: replace with actual role IDs (integers)
    1430761119689211934
]

# ID of the text channel where the bot will send the custom message / logs:
LOG_CHANNEL_ID = 1399460846379466782  # replace with your channel ID

# Custom message sent to LOG_CHANNEL when a ban happens.
# Available placeholders in the string: {user}, {user_id}, {guild}, {role}
CUSTOM_MESSAGE = "Banned {user} (ID: {user_id}) had role {role}"

# Safety: start in dry-run mode so it does not actually ban until you set False
DRY_RUN = False
# ------------------------------------------------------------

intents = discord.Intents.default()
intents.members = True  # REQUIRED: enable "Server Members Intent" in the dev portal
bot = commands.Bot(command_prefix="!", intents=intents)

async def send_log(guild: discord.Guild, content: str):
    """Send content to the configured log channel in the guild, if found."""
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        try:
            await ch.send(content)
        except Exception as e:
            print(f"[{guild.name}] Failed to send log message: {e}\nContent: {content}")
    else:
        # fallback to printing to console if channel ID not found in that guild
        print(f"[{guild.name}] LOG CHANNEL NOT FOUND. Would send: {content}")

async def try_ban_member(member: discord.Member, detected_role: discord.Role):
    """
    Attempt to ban member if they have a forbidden role.
    Returns True if action (ban or dry-run log) was taken, False otherwise.
    """
    guild = member.guild

    # never ban the server owner
    if member == guild.owner:
        await send_log(guild, f"Skipped banning server owner: {member} ({member.id})")
        return False

    # Confirm the member currently has the role (race conditions)
    if not any(r.id in FORBIDDEN_ROLE_IDS for r in member.roles):
        return False

    # Dry-run: just report
    if DRY_RUN:
        msg = CUSTOM_MESSAGE.format(user=member.mention, user_id=member.id, guild=guild.name, role=detected_role.name)
        await send_log(guild, "(dry-run) " + msg)
        print(f"(dry-run) Would ban {member} ({member.id}) for role {detected_role.name} in {guild.name}")
        return True

    # Ensure bot can ban (role hierarchy)
    me = guild.me
    if me is None:
        await send_log(guild, f"Bot member object missing; can't ban {member}.")
        return False

    if member.top_role >= me.top_role:
        await send_log(guild, f"Cannot ban {member} ({member.id}) because their top role >= bot's top role.")
        return False

    # Attempt ban
    try:
        await guild.ban(member, reason=f"Auto-ban: had forbidden role {detected_role.name} ({detected_role.id})")
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
    # If a joining member already has any forbidden role, act
    for r in member.roles:
        if r.id in FORBIDDEN_ROLE_IDS:
            await try_ban_member(member, r)
            break

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # detect role additions
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    added = after_ids - before_ids
    if not added:
        return
    # if any added role is forbidden, act on the user (pick the forbidden role object for message)
    for role_id in added:
        if role_id in FORBIDDEN_ROLE_IDS:
            role_obj = after.guild.get_role(role_id)
            await try_ban_member(after, role_obj or discord.Object(id=role_id))
            return

# Optional command to quickly show configuration (owner/admin only)
@bot.command()
@commands.is_owner()
async def show_config(ctx):
    await ctx.send(
        f"FORBIDDEN_ROLE_IDS: {FORBIDDEN_ROLE_IDS}\n"
        f"LOG_CHANNEL_ID: {LOG_CHANNEL_ID}\n"
        f"DRY_RUN: {DRY_RUN}"
    )

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERROR: please set BOT_TOKEN environment variable to your bot token before running.")
        raise SystemExit(1)
    bot.run(token)
