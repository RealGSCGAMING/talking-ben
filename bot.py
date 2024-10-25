import discord
from discord.ext import commands
import random
import os
import json

# Load the token from config.json
with open('config.json') as config_file:
    config = json.load(config_file)
    TOKEN = config['token']

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # Enable voice state intents

bot = commands.Bot(command_prefix="!", intents=intents)

# Folder path for sound effects
SOUNDS_FOLDER = "Sounds"
SOUNDS = {
    "arrive": os.path.join(SOUNDS_FOLDER, "Arrive.mp3"),
    "leave": os.path.join(SOUNDS_FOLDER, "Leave.mp3"),
    "yes": os.path.join(SOUNDS_FOLDER, "Yes.mp3"),
    "no": os.path.join(SOUNDS_FOLDER, "No.mp3"),
    "laugh": os.path.join(SOUNDS_FOLDER, "Laugh.mp3"),
    "ugh": os.path.join(SOUNDS_FOLDER, "Ugh.mp3")
}

@bot.command(name="join")
async def join(ctx, *, channel: str):
    # Try to convert the channel to an ID first
    channel_id = None
    try:
        channel_id = int(channel)
    except ValueError:
        # If it can't be converted, search for the channel by name
        for ch in ctx.guild.voice_channels:
            if ch.name.lower() == channel.lower():
                channel_id = ch.id
                break

    if channel_id is None:
        await ctx.send("Could not find a voice channel with that name or ID.")
        return

    channel = ctx.guild.get_channel(channel_id)
    if ctx.guild.voice_client is not None:
        return await ctx.send("The bot is already in a voice channel!")

    await channel.connect()
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["arrive"]))
    await ctx.send(f"Joined {channel.name}!")

@bot.command(name="leave")
async def leave(ctx):
    if ctx.guild.voice_client is None:
        return await ctx.send("The bot is not in a voice channel!")

    ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["leave"]))
    await ctx.guild.voice_client.disconnect()
    await ctx.send("Left the voice channel!")

@bot.command(name="ask")
async def ask(ctx, *, question: str):
    if ctx.guild.voice_client is None:
        return await ctx.send("The bot needs to be in a voice channel first! Use `!join`.")

    responses = ["yes", "no", "laugh", "ugh"]
    selected_response = random.choice(responses)
    ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS[selected_response]))
    await ctx.send(f"Ben's response: {selected_response.capitalize()}!")

# Run the bot
bot.run(TOKEN)
