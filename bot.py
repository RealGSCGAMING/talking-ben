import os
import json
import discord
from discord.ext import commands
import random
import asyncio
from flask import Flask, jsonify, render_template_string, send_from_directory
from threading import Thread
import threading
from gtts import gTTS
import tempfile

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

SOUNDS = {
    "arrive": "Sounds/Arrive.mp3",
    "leave": "Sounds/Leave.mp3",
    "yes": "Sounds/Yes.mp3",
    "no": "Sounds/No.mp3",
    "laugh": "Sounds/Laugh.mp3",
    "ugh": "Sounds/Ugh.mp3",
    "ksi": "Sounds/KSI.mp3"
}


app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory(os.getcwd(), "botsite.html")

def run_flask():
    app.run(host="0.0.0.0", port=5000)

threading.Thread(target=run_flask).start()

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
    else:
        await ctx.send("Please provide a valid channel name or ID.")

@bot.command(name="leave")
async def leave(ctx):
    """Leaves the voice channel."""
    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["leave"]))
        while ctx.guild.voice_client.is_playing():
            await asyncio.sleep(1)
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

from gtts import gTTS
import tempfile

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    """Asks Ben a question."""

    user_nickname = ctx.author.display_name
    tts_text = f"{user_nickname} asked: {question}"

    # Generate TTS audio using gtts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_audio:
        tts = gTTS(tts_text, lang='en')
        tts.save(tts_audio.name)
    
    # Choose a response audio file
    response = random.choice(["yes", "no", "laugh", "ugh"])
    response_audio_path = SOUNDS[response]

    # Play TTS message first, then response audio
    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(tts_audio.name), 
                                    after=lambda e: ctx.guild.voice_client.play(discord.FFmpegPCMAudio(response_audio_path)))
        await ctx.reply(f"Ben says: {response.capitalize()}")

    # Clean up TTS audio file after it's used
    os.remove(tts_audio.name)


@bot.command(name="commands")
async def commands(ctx):
    """Lists all commands with their syntax and descriptions."""
    command_descriptions = [
        "**b.commands** - Shows this list of commands.",
        "**b.join [channel name/ID]** - Joins the specified voice channel.",
        "**b.leave** - Leaves the current voice channel.",
        "**b.ask [question]** - Asks Ben a question. If Ben is in a voice channel, he will play a response.",
        "**b.ping** - Checks the bot's latency.",
    ]
    await ctx.send("\n".join(command_descriptions))

@bot.command(name="ping")
async def ping(ctx):
    """Checks the bot's ping time."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency is {latency}ms")

@bot.command(name="aski")
async def aski(ctx):
    """I'm in the thick of it, everybody knows..."""
    special_response = "from the screen 🖥️ to the ring 💍 to the pen 🖊️ to the king 🤴(⚔️) wheres my crown 👑 thats my bling 💎 always trouble when i reign 👊😈"
    await ctx.reply(f"Ben says: {special_response}")

    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["ksi"]))


bot.run(TOKEN)