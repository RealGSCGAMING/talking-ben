import os
import json
import discord
from discord.ext import commands
import random
import asyncio
from flask import Flask, jsonify
from threading import Thread

# Load token function
def load_token():
    try:
        with open("config.json") as config_file:
            config = json.load(config_file)
            return config.get("token")
    except FileNotFoundError:
        return None

TOKEN = load_token()
if not TOKEN:
    TOKEN = os.getenv("token")
if not TOKEN:
    raise ValueError("No token found in config.json or environment variable.")

intents = discord.Intents.all()
intents.voice_states = True
bot = commands.Bot(command_prefix="b.", intents=intents)

# Path to sound files
SOUNDS = {
    "arrive": "Sounds/Arrive.mp3",
    "leave": "Sounds/Leave.mp3",
    "yes": "Sounds/Yes.mp3",
    "no": "Sounds/No.mp3",
    "laugh": "Sounds/Laugh.mp3",
    "ugh": "Sounds/Ugh.mp3"
}

# Global variables for presets and permissions
default_channel = None
permission_level = 0
restricted_role = None

# Flask setup
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify(status="Bot is running", latency=f"{round(bot.latency * 1000)}ms" if bot.is_ready() else "N/A")

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Start Flask in a separate thread
flask_thread = Thread(target=run_flask)
flask_thread.start()

# Role and preset commands
@bot.command(name="preset")
async def preset(ctx, *, channel_name: str):
    """Set or clear a default channel for Ben to join."""
    global default_channel

    # Admin or required role check
    if not await has_permission(ctx, level=0):
        return

    # Set default channel or turn it off
    if channel_name.lower() == "off":
        default_channel = None
        await ctx.send("Default channel preset has been turned off.")
    else:
        channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)
        if channel:
            default_channel = channel
            await ctx.send(f"Default channel preset set to: {channel.mention}")
        else:
            await ctx.send(f"Channel '{channel_name}' not found.")

@bot.command(name="role")
async def role(ctx, level: int, *, role_name: str = None):
    """Set permissions level for bot control and restrict commands to a role."""
    global permission_level, restricted_role

    if not await has_permission(ctx, level=0):
        return

    # Set the permission level
    if level in [0, 1, 2]:
        permission_level = level
    else:
        await ctx.send("Invalid level. Use 0, 1, or 2.")
        return

    # Find and set the restricted role, or default to server managers
    if role_name:
        restricted_role = discord.utils.get(ctx.guild.roles, name=role_name) or ctx.guild.get_role(int(role_name))
        if restricted_role:
            await ctx.send(f"{restricted_role.mention} has been given control of Ben with permission level {level}.")
        else:
            await ctx.send(f"Role '{role_name}' not found.")
            restricted_role = None
    else:
        restricted_role = None
        await ctx.send("No role specified; only users with 'Manage Server' can control Ben at this level.")

async def has_permission(ctx, level):
    """Check if the user has the required role or Manage Server permission."""
    if permission_level > level:
        return True  # Command requires a lower level than current setting

    user_role = ctx.guild.get_role(restricted_role.id) if restricted_role else None
    if user_role in ctx.author.roles or ctx.author.guild_permissions.manage_guild:
        return True
    else:
        await ctx.send(f"Only {restricted_role.mention if restricted_role else 'users with Manage Server permission'} can use this command.")
        return False

@bot.command(name="join")
async def join(ctx, *, channel_name: str = None):
    """Joins a voice channel, with optional preset support."""
    if not await has_permission(ctx, level=1):
        return

    # Check if bot is already connected
    if ctx.guild.voice_client:
        await ctx.send("Ben is already in a voice channel.")
        return

    # Use specified channel or preset channel
    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name) if channel_name else default_channel

    if channel:
        await channel.connect()
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["arrive"]))
        await ctx.send(f"Joined {channel.name}!")
    else:
        await ctx.send("Please provide a valid channel name or set a default channel using b.preset")

@bot.command(name="leave")
async def leave(ctx):
    """Leaves the voice channel."""
    if not await has_permission(ctx, level=1):
        return

    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["leave"]))
        while ctx.guild.voice_client.is_playing():
            await asyncio.sleep(1)
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    """Asks Ben a question, replies to user, and plays response if in channel."""
    if not await has_permission(ctx, level=2):
        return

    response = random.choice(["yes", "no", "laugh", "ugh"])
    await ctx.reply(f"Ben says: {response.capitalize()}")

    # Play audio if bot is in a voice channel
    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS[response]))

@bot.command(name="commands")
async def commands(ctx):
    """Lists all commands with their syntax and descriptions."""
    command_descriptions = [
        "**b.commands** - Shows a list of all commands and their syntax.",
        "**b.join [channel name/ID]** - Joins the specified voice channel. If no channel is specified, joins the preset channel if one is set.",
        "**b.leave** - Leaves the current voice channel.",
        "**b.ask [question]** - Asks Ben a question. If Ben is in a voice channel, he will play a response.",
        "**b.preset [channel name/ID/off]** - Sets a default voice channel for Ben to join with `b.join`. Use 'off' to remove the preset.",
        "**b.role [level (0/1/2)] [role name/ID]** - Sets role-based permissions for bot commands. Level 0 locks `b.role` and `b.preset`; level 1 adds `b.join` and `b.leave`; level 2 locks all commands.",
        "**b.ping** - Checks the bot's latency.",
    ]
    await ctx.send("\n".join(command_descriptions))

@bot.command(name="ping")
async def ping(ctx):
    """Checks the bot's ping time."""
    latency = round(bot.latency * 1000)  # Convert to milliseconds
    await ctx.send(f"Pong! Latency is {latency}ms")

# Run the bot
bot.run(TOKEN)