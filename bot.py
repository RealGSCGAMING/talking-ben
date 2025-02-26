import os
import json
import discord
from discord.ext import commands
import random
import asyncio
from gtts import gTTS
import tempfile

# Load the bot token
def load_token():
    try:
        with open("config.json") as config_file:
            config = json.load(config_file)
            return config.get("token")
    except FileNotFoundError:
        return None

TOKEN = load_token() or os.getenv("token")
if not TOKEN:
    raise ValueError("No token found in config.json or environment variable.")

# Set up bot intents and instance
intents = discord.Intents.all()
intents.voice_states = True
bot = commands.Bot(command_prefix="b.", intents=intents)

# Predefined sound effects
SOUNDS = {
    "arrive": "Sounds/Arrive.mp3",
    "leave": "Sounds/Leave.mp3",
    "yes": "Sounds/Yes.mp3",
    "no": "Sounds/No.mp3",
    "laugh": "Sounds/Laugh.mp3",
    "ugh": "Sounds/Ugh.mp3",
    "ksi": "Sounds/KSI.mp3"
}

@bot.event
async def on_ready():   
    print(f"(!) - Logged in as {bot.user}")

# Bot commands
@bot.command(name="join")
async def join(ctx, *, channel_name: str = None):
    """Joins a voice channel."""
    if ctx.guild.voice_client:
        await ctx.send("Ben is already in a voice channel.")
        return

    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)
    if channel:
        await channel.connect()
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["arrive"]))
        await ctx.send(f"Joined {channel.name}!")
        print(f"(!) - Joined channel: {channel.name}")
    else:
        await ctx.send("Please provide a valid channel name or ID.")

@bot.command(name="leave")
async def leave(ctx):
    """Leaves the voice channel."""
    voice_client = ctx.guild.voice_client
    if voice_client:
        voice_client.play(discord.FFmpegPCMAudio(SOUNDS["leave"]))
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()
        await ctx.send("Left the voice channel.")
        print(f"(!) - Left channel")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    """Asks Ben a question with TTS and random response sound."""
    user_nickname = ctx.author.display_name
    tts_text = f"{user_nickname} asked: {question}"

    # Generate TTS audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_audio:
        gTTS(tts_text, lang='en').save(tts_audio.name)
        tts_filename = tts_audio.name

    response = random.choice(["yes", "no", "laugh", "ugh"])
    response_audio_path = SOUNDS[response]

    voice_client = ctx.guild.voice_client
    if voice_client:
        def cleanup(_):
            # Safely delete the file after playback finishes
            try:
                os.remove(tts_filename)
            except Exception as e:
                print(f"Error deleting TTS file: {e}")

        def play_response(_):
            # Play the response sound after TTS
            voice_client.play(
                discord.FFmpegPCMAudio(response_audio_path),
                after=cleanup
            )

        voice_client.play(
            discord.FFmpegPCMAudio(tts_filename),
            after=play_response
        )

        await ctx.reply(f"Ben says: {response.capitalize()}")
        print(f"(!) - {user_nickname} asked: {question}")
        print(f"(!) - Response: {response.capitalize()}")



@bot.command(name="commands")
async def commands_list(ctx):
    """Lists all bot commands."""
    command_descriptions = [
        "**b.commands** - Shows this list of commands.",
        "**b.join [channel name/ID]** - Joins the specified voice channel.",
        "**b.leave** - Leaves the current voice channel.",
        "**b.ask [question]** - Asks Ben a question with audio response.",
        "**b.ping** - Checks the bot's latency.",
    ]
    await ctx.send("\n".join(command_descriptions))

@bot.command(name="ping")
async def ping(ctx):
    """Checks latency."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency is {latency}ms")

@bot.command(name="aski")
async def aski(ctx):
    """Special phrase with audio playback."""
    special_response = (
        "from the screen 🖥️ to the ring 💍 to the pen 🖊️ to the king 🤴(⚔️) "
        "wheres my crown 👑 thats my bling 💎 always trouble when i reign 👊😈"
    )
    await ctx.reply(f"Ben says: {special_response}")
    print(f"(!) - Played KSI response")

    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["ksi"]))

# Run the bot
bot.run(TOKEN)