import os
import json
import discord
from discord.ext import commands
import random
import asyncio
from flask import Flask
from threading import Thread

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
    TOKEN = os.getenv("token")

# Check if we successfully retrieved a token
if not TOKEN:
    raise ValueError("No token found in config.json or environment variable.")

# Set up intents
intents = discord.Intents.all()
intents.voice_states = True  # Needed to join and leave voice channels

# Set up the bot with the new prefix and intents
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

# Inactivity timer
inactive_timer = None

async def reset_inactivity_timer(ctx):
    global inactive_timer
    if inactive_timer is not None:
        inactive_timer.cancel()
    inactive_timer = bot.loop.create_task(asyncio.sleep(300))  # 5 minutes

@bot.event
async def on_command(ctx):
    """Resets the inactivity timer when a command is run."""
    await reset_inactivity_timer(ctx)

@bot.command(name="join")
async def join(ctx, *, channel_name: str = None):
    """Joins a voice channel."""
    global inactive_timer

    # Check if a channel name was provided
    if channel_name is None:
        await ctx.send("You need to provide a channel name! Use b.join [channel]")
        return

    # Check if the bot is already in a voice channel
    if ctx.guild.voice_client:
        await ctx.send("I'm already in a voice channel.")
        return

    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)

    if channel:
        await channel.connect()
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["arrive"]))
        await ctx.send(f"Joined {channel.name}!")
        await reset_inactivity_timer(ctx)  # Reset timer on join
    else:
        await ctx.send(f"Channel '{channel_name}' not found.")

@bot.command(name="leave")
async def leave(ctx):
    """Leaves the voice channel."""
    global inactive_timer
    if ctx.guild.voice_client:
        # Play the leave sound
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["leave"]))

        # Wait for the sound to finish before disconnecting
        while ctx.guild.voice_client.is_playing():
            await asyncio.sleep(1)  # Wait for 1 second

        await ctx.guild.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
        inactive_timer.cancel()  # Stop the timer when leaving
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    """Asks Ben a question. Replies directly to the user, with audio if in a voice channel."""
    response = random.choice(["yes", "no", "laugh", "ugh"])  # Placeholder logic

    # Check if the bot is in a voice channel
    if ctx.guild.voice_client:
        # Play the response sound if connected to a voice channel
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS[response]))

    # Reply to the user with the response text
    await ctx.reply(f"Ben says: {response.capitalize()}", mention_author=True)
    
    # Reset the inactivity timer since a command was used
    await reset_inactivity_timer(ctx)

@bot.command(name="ping")
async def ping(ctx):
    """Checks the bot's ping time."""
    latency = round(bot.latency * 1000)  # Convert to milliseconds
    await ctx.send(f"Pong! Latency is {latency}ms")

@bot.command(name="commands")  # Changed from help to commands
async def commands_list(ctx):
    """Sends a list of commands and their descriptions."""
    help_text = (
        "Here are my commands:\n"
        "b.join [channel name or id] - Joins the specified voice channel.\n"
        "b.leave - Leaves the voice channel.\n"
        "b.ask [question] - Asks Ben a question and gets a response.\n"
        "b.ping - Checks the bot's ping time.\n"
        "b.commands - Displays this help message."  # Updated to match command name
    )
    await ctx.send(help_text)

async def inactivity_check():
    """Checks for inactivity and leaves the voice channel if no commands are run."""
    global inactive_timer
    while True:
        await asyncio.sleep(1)  # Check every second
        if inactive_timer is not None and inactive_timer.done():
            # If timer is done, leave the voice channel
            for guild in bot.guilds:
                if guild.voice_client:
                    await guild.voice_client.disconnect()
                    await guild.text_channels[0].send("Ben disconnected due to inactivity.")
            inactive_timer = None  # Reset the timer

@bot.before_invoke
async def before_invoke(ctx):
    """Set up the inactivity check before any command is invoked."""
    bot.loop.create_task(inactivity_check())

# Set up the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Function to run the Flask app
def run_web_server():
    port = int(os.environ.get("PORT", 5000))  # Render provides a PORT env variable
    app.run(host="0.0.0.0", port=port)

# Start the web server in a separate thread
web_thread = Thread(target=run_web_server)
web_thread.start()

# Run the bot
bot.run(TOKEN)