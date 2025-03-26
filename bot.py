import os
import json
import discord
from discord.ext import commands
import random
import asyncio
from gtts import gTTS
import tempfile


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


intents = discord.Intents.all()
intents.voice_states = True
bot = commands.Bot(command_prefix="b.", intents=intents)



text_to_speech = False
easter_egg = False
restrict_joining = False
restrict_speaking = False

def load_settings():
    try:
        with open("settings.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "Text To Speech": True,
            "Easter Egg": True,
            "Restrict Joining": False,
            "Restrict Speaking": False
        }

def save_settings():
    with open("settings.json", "w") as file:
        json.dump(settings_state, file, indent=4)

def apply_settings():
    global text_to_speech, easter_egg, restrict_joining, restrict_speaking
    text_to_speech = settings_state["Text To Speech"]
    easter_egg = settings_state["Easter Egg"]
    restrict_joining = settings_state["Restrict Joining"]
    restrict_speaking = settings_state["Restrict Speaking"]

settings_state = load_settings()
apply_settings()

def get_settings_options():
    return [
        discord.SelectOption(label=f"Text To Speech - {'Enabled' if settings_state['Text To Speech'] else 'Disabled'}", description="Controls text-to-speech before responses."),
        discord.SelectOption(label=f"Easter Egg - {'Enabled' if settings_state['Easter Egg'] else 'Disabled'}", description="Controls the bot's secret easter egg."),
        discord.SelectOption(label=f"Restrict Joining - {'Enabled' if settings_state['Restrict Joining'] else 'Disabled'}", description="Requires Manage Server permission for b.join and b.leave."),
        discord.SelectOption(label=f"Restrict Speaking - {'Enabled' if settings_state['Restrict Speaking'] else 'Disabled'}", description="Requires Manage Server permission for b.ask."),
        discord.SelectOption(label="Close", description="Removes this menu.")
    ]

class SettingsView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author
        self.add_item(SettingsDropdown(author))

class SettingsDropdown(discord.ui.Select):
    def __init__(self, author: discord.Member):
        self.author = author
        super().__init__(placeholder="Select a setting...", options=get_settings_options())

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("This menu is not for you.", ephemeral=True)
            return

        setting_name = self.values[0].split(" - ")[0]
        if setting_name in settings_state:
            settings_state[setting_name] = not settings_state[setting_name]
            save_settings()
            apply_settings()
            await interaction.response.send_message(f"{setting_name} is now {'Enabled' if settings_state[setting_name] else 'Disabled'}.", ephemeral=True)
            
            self.view.clear_items()
            self.view.add_item(SettingsDropdown(self.author))
            await interaction.message.edit(view=self.view)
        elif setting_name == "Close":
            await interaction.message.delete()

@bot.command(name="settings")
@commands.has_permissions(manage_guild=True)
async def settings(ctx, setting: str = None, value: str = None):
    """Allows server admins to configure bot settings."""
    setting_map = {
        "tts": "Text To Speech",
        "egg": "Easter Egg",
        "joining": "Restrict Joining",
        "speaking": "Restrict Speaking"
    }
    
    if setting and value:
        setting_name = setting_map.get(setting.lower())
        if setting_name and value.lower() in ["true", "false"]:
            settings_state[setting_name] = value.lower() == "true"
            save_settings()
            apply_settings()
            print(f"(!) - {setting_name} is now {'Enabled' if settings_state[setting_name] else 'Disabled'}.")
            msg = await ctx.send(f"{setting_name} is now {'Enabled' if settings_state[setting_name] else 'Disabled'}.")
            await asyncio.sleep(3)
            await msg.delete()
            return
    
    embed = discord.Embed(title="Settings", description="Click a setting in the dropdown to toggle it.", color=discord.Color.blue())
    view = SettingsView(ctx.author)
    await ctx.send(embed=embed, view=view)

@settings.error
async def settings_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need the \"Manage Server\" permission to use this command.", ephemeral=True)



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



@bot.command(name="join")
async def join(ctx, *, channel_name: str = None):
    """Joins a voice channel."""
    if restrict_joining and not ctx.author.guild_permissions.manage_guild:
        return
    
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
    if restrict_joining and not ctx.author.guild_permissions.manage_guild:
        return
    
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
    """Asks Ben a question with optional TTS and a random response sound."""
    if restrict_speaking and not ctx.author.guild_permissions.manage_guild:
        return
    
    user_nickname = ctx.author.display_name
    tts_text = f"{user_nickname} asked: {question}"
    response = random.choice(["yes", "no", "laugh", "ugh"])
    response_audio_path = SOUNDS[response]

    voice_client = ctx.guild.voice_client
    if voice_client:
        def cleanup(_):
            
            if text_to_speech:
                try:
                    os.remove(tts_filename)
                except Exception as e:
                    print(f"Error deleting TTS file: {e}")

        def play_response(_):
            
            voice_client.play(
                discord.FFmpegPCMAudio(response_audio_path),
                after=None
            )

        if text_to_speech:
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tts_audio:
                gTTS(tts_text, lang='en').save(tts_audio.name)
                tts_filename = tts_audio.name

            voice_client.play(
    discord.FFmpegPCMAudio(
        tts_filename 
        #, options="-filter:a 'asetrate=44100*1.05,atempo=1.0'"
        # first number after 40000: pitch | second number: speed
    ),
    after=play_response
)


        else:
            play_response(None)

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
        "**b.settings** - Allows server managers to change bot settings.",
        "**b.ping** - Checks the bot's latency."
    ]
    await ctx.send("\n".join(command_descriptions))

@bot.command(name="ping")
async def ping(ctx):
    """Checks latency."""
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency is {latency}ms")

@bot.command(name="aski")
async def aski(ctx):
    """Funny."""
    if not easter_egg:
        return

    special_response = (
        "from the screen 🖥️ to the ring 💍 to the pen 🖊️ to the king 🤴(⚔️) "
        "wheres my crown 👑 thats my bling 💎 always trouble when i reign 👊😈"
    )
    await ctx.reply(f"Ben says: {special_response}")
    print(f"(!) - Played KSI response")

    if ctx.guild.voice_client:
        ctx.guild.voice_client.play(discord.FFmpegPCMAudio(SOUNDS["ksi"]))



bot.run(TOKEN)