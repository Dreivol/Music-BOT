import discord
from discord.ext import commands
import os
from requests_html import HTMLSession
import yt_dlp
import logging
import asyncio

logger = logging.getLogger("my_bot")

# Create a Discord Intents object that enables all events to be received
intents = discord.Intents().all()

# Create a new Bot instance with command prefix "-" and intents
bot = commands.Bot(command_prefix="-", intents=intents)


@bot.event
async def on_ready():
    print('Bot Online')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='Music | -help'))
    print('Bot is connected to the following servers:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')


async def join_voice_channel(ctx):

    # Check if the user is in a voice channel
    if not ctx.message.author.voice:
        await ctx.send("*You're not in a voice channel*")
        return False

    # Get the voice channel object
    channel = ctx.message.author.voice.channel

    # Connect to the voice channel
    try:
        voice_client = await channel.connect()

    # Prints exception if failed to connect
    except Exception as e:
        await ctx.send(f"*Failed to connect to voice channel: {e}*")
        return False

    # Return function successful
    return True


# Play Function
async def play_song(ctx, url, action=None):
    # ... existing code ...

    if action == "pause":
        # Pause the current song if it's playing
        if voice.is_playing():
            voice.pause()
            await ctx.send("*Song paused*")
        else:
            await ctx.send("*No song is currently playing*")
        return

    elif action == "resume":
        # Resume the current song if it's paused
        if voice.is_paused():
            voice.resume()
            await ctx.send("*Song resumed*")
        else:
            await ctx.send("*No song is currently paused*")
        return

    # Check if the "songs" directory exists, if not create it
    if not os.path.exists("songs"):
        os.makedirs("songs")

    # Get the bot's voice client for where the command was invoked
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Check if a song is already playing
    song_there = os.path.isfile("songs/song.mp3")

    # Join/move voice channel
    try:
        # If the bot is already connected to a voice channel, move to the user's channel
        if voice and voice.is_connected():
            await voice.move_to(ctx.author.voice.channel)
        # If the bot is not connected to a voice channel, join the user's channel
        else:
            await join_voice_channel(ctx)

            # Get the bot's voice client again after joining the channel
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        # If voice is None, the bot failed to join a voice channel
        if voice is None:
            await ctx.send("*Failed to join a voice channel*")
            return

    except:
        # If there was an error joining the voice channel, send a message to the user
        await ctx.send("*Failed to join the voice channel*")
        return

    # Download the song from YouTube
    # await ctx.send("*Downloading song files...*")
    # Configures ydl
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "songs/%(title)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Uses ydl to extract the title
        info_dict = ydl.extract_info(url, download=False)
        title = info_dict.get("title", "song")

        # Check if the file already exists before downloading it
        if not os.path.isfile(f"songs/{title}.mp3"):
            ydl.download([url])

    # Add the downloaded song to the queue
    if voice.is_playing():
        queue.append(title)
        position = len(queue)

        embed = discord.Embed(
            title="Added to queue",
            description=(f"{title} is in position #{position}"),
            color=discord.Color.yellow(),
        )
        # Send successful queue notification
        await ctx.send(embed=embed)
    else:
        queue.append(title)
        position = 0

    # If there is no song playing, start playing the queued songs
    if not voice.is_playing():
        await play_next(ctx)


# Initialize queue array
queue = []

# Play the next song function


async def play_next(ctx):

    # Get the bot's voice client for where the command was invoked
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    # Check if queue is empty
    if not queue:
        # Wait 600s
        await asyncio.sleep(600)
        # Check if queue is still empty, if so, disconnect
        if not queue:
            await voice.disconnect()
            return

    # Get first song
    next_song = queue.pop(0)

    try:
        # Play the next song
        voice.play(
            discord.FFmpegPCMAudio(f"songs/{next_song}.mp3"),
            after=lambda e: bot.loop.create_task(
                play_next(ctx)) if not ctx.voice_client.is_playing() else None
        )

        # Set the volume of the song to 30%
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.3
        # Send a message to the user indicating that the next song is playing
        # Create an embedded message with information about the current song
        embed = discord.Embed(
            title="Now Playing", description=f"{next_song}", color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
    except:
        # If there was an error playing the next song, send a message to the user
        await ctx.send("*The queue is now empty*")
    return


# Play command
@bot.command(aliases=["p", "gelgel"])
async def play(ctx, *, query_or_url):
    """
    Plays the audio directly from YouTube
    """

    # Check if the argument is a valid YouTube URL
    if "youtube.com/watch?v=" in query_or_url or "youtu.be/" in query_or_url:
        # If it's a valid URL, call the play_song function
        await play_song(ctx, query_or_url)

    else:
        # If it's not a URL, assume it's a search query
        # await ctx.send(f"*Searching for `{query_or_url}` on YouTube...*")

        # Use yt_dlp to search for videos matching the query
        with yt_dlp.YoutubeDL() as ydl:
            try:
                # Search YouTube for the best match
                info = ydl.extract_info(f"ytsearch:{query_or_url}", download=False)[
                    "entries"
                ][0]
                url = info["webpage_url"]

                # Send a message to the user indicating the found video
                # await ctx.send(f"*Found `{info['title']}`*")

                # Call the play_song function with the found video URL
                await play_song(ctx, url)
            except:
                # If there was an error searching for videos or extracting information, send a message to the user
                await ctx.send(
                    "*There was an error searching for videos (or extracting info).*"
                )


# Skip command
@bot.command()
async def skip(ctx):
    """
    Skips the current song, playing the next one in queue if there is one.
    """

    # Get the voice client info
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    # Stop playing audio
    voice.stop()
    # Play the next song in queue
    await play_next(ctx)


@bot.command(aliases=["queue"])
async def q(ctx):
    """
    Shows which songs are in the queue.
    """

    # Check if queue is empty
    if not queue:
        # Create an embed with a title and description indicating that the queue is empty
        embed = discord.Embed(
            title="Queue",
            description="The queue is currently empty",
            color=discord.Color.lighter_grey(),
        )
        await ctx.send(embed=embed)
        return

    # Create a list of strings containing the current song queue using tuples
    queue_list = [f"**{i+1}**. {song}" for i, song in enumerate(queue)]

    # Create a string containing the list of songs separated by line breaks
    queue_string = "\n".join(queue_list)

    # Create an embed with a title and description containing the current song queue
    embed = discord.Embed(
        title="Queue", description=queue_string, color=discord.Color.lighter_grey()
    )

    # Send the embed to the user
    await ctx.send(embed=embed)


@bot.command(name='pause', help='Pause the currently playing song')
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        if isinstance(voice.source, discord.FFmpegPCMAudio):
            title = voice.source.title
            requester = voice.source.requester
            embed = discord.Embed(
                title="Paused",
                description=f"Paused {title} by {requester}",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="Paused",
                description="The player has been paused.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Already Paused",
            description="The player is not playing anything at the moment.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


@bot.command(name='resume', help='Resume the currently playing song.')
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        if isinstance(voice.source, discord.FFmpegPCMAudio):
            title = voice.source.title
            requester = voice.source.requester
            embed = discord.Embed(
                title="Resumed",
                description=f"Resumed {title} by {requester}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Resumed",
                description="The player has been resumed.",
                color=discord.Color.green()
            )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Already Resuming",
            description="The player is not paused at the moment.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


@bot.command(name="leave", aliases=["siktir", "defol"], help="Leave the voice channels.")
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        await voice.disconnect()
        await ctx.message.add_reaction("👋")
    else:
        await ctx.send("The bot is not connected to a voice channel.")

bot.run("YOUR TOKEN")
