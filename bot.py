import os
import json
import discord
from discord.ext import commands

# Function to load the token from config.json
def load_token():
    try:
        with open("config.json") as config_file:
            config = json.load(config_file)
            return config.get("token")  # Get the token from config.json
    except FileNotFoundError:
        return None  # If config.json doesn't exist, return None

# Load the token
TOKEN = load_token()

# If token is None, fallback to environment variable
if not TOKEN:
    TOKEN = os.getenv("TOKEN")

# Check if we successfully retrieved a token
if not TOKEN:
    raise ValueError("No token found in config.json or environment variable.")

# Set up the bot with the new prefix
bot = commands.Bot(command_prefix="b!")

# Path to sound files
SOUNDS = {
    "arrive": "Sounds/Arrive.mp3",
    "leave": "Sounds/Leave.mp3",
    "yes": "Sounds/Yes.mp3",
    "no": "Sounds/No.mp3",
    "laugh": "Sounds/Laugh.mp3",
    "ugh": "Sounds/Ugh.mp3"
}

@bot.command(name="join")
async def join(ctx, *, channel_name: str):
    """Joins a voice channel."""
    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)

    # If channel is found by name
    if channel:
        await channel.connect()
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["arrive"]))
        await ctx.send(f"Joined {channel.name}!")
    else:
        await ctx.send(f"Channel '{channel_name}' not found.")

@bot.command(name="leave")
async def leave(ctx):
    """Leaves the voice channel."""
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["leave"]))
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    """Asks Ben a question."""
    if ctx.guild.voice_client:
        # Play a random sound based on the question (this is a placeholder logic)
        response = random.choice(["yes", "no", "laugh", "ugh"])  # Replace with your logic
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS[response]))
        await ctx.send(f"Ben says: {response.capitalize()}")
    else:
        await ctx.send("The bot needs to be in a voice channel first! (Use b!join [channel])")

# Run the bot
bot.run(TOKEN)