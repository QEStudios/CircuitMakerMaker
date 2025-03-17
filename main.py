from render import render
from uwuify import uwuify_string
import generate
import discord
from discord import option
from discord.ext import commands
from dotenv import load_dotenv
import os
import io
import traceback
import regex as re
import requests
import aiohttp
import time
import asyncio
import json
import feedparser
import ffmpeg
from pytubefix import YouTube
from PIL import Image
import subprocess
from datetime import datetime
import pytz

load_dotenv()

TOKEN = os.getenv("TOKEN")
DPASTE_AUTH = os.getenv("DPASTE_AUTH")

DPASTE_HEADERS = {
    "User-Agent": "Circuit Maker Maker Discord Bot (contact: qestudios17@gmail.com or @skmgeek on discord)",
    "Authorization": f"Bearer {DPASTE_AUTH}",
}

youtube_channels = [
    "UCvL2QwDXWFJn1J5aNjaUczw",  # Daytell
    "UCUdeaj2BNwbM3qa-u705a4w",  # Today's Number
    "UCU5Cd2fKEvidHzxjj4UIiug",  # Are Things Swell
]

melbourne_tz = pytz.timezone("Australia/Melbourne")

intents = discord.Intents.all()

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print(f"Bot ID: {bot.user.id}")
    print("-----")
    game = discord.Game("Circuit Maker 2")
    await bot.change_presence(activity=game)


@bot.slash_command(description="Get the UserId for a roblox username.")
async def getuser(ctx, username: str):
    await ctx.defer()
    userUrl = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    async with aiohttp.ClientSession() as session:
        async with session.post(userUrl, json=payload) as res:
            if res.status != 200:
                await ctx.respond(
                    "There was an error contacting Roblox API. Please try again later.",
                    ephemeral=True,
                )
                return
            resJson = await res.json()
    if len(resJson["data"]) == 0:
        await ctx.respond("Invalid username.", ephemeral=True)
    userId = resJson["data"][0]["id"]
    await ctx.respond(str(userId), ephemeral=True)


def saveToBytes(save):
    saveString = save.exportSave()
    file = discord.File(io.BytesIO(saveString.encode()), filename=f"generated.txt")
    return file


generateCommand = bot.create_group(
    "generate", "Automatically generate circuits from parameters."
)


@generateCommand.command(description="A clock with a given period.")
@option(
    "period",
    description="The period of the clock, in ticks/cycle.",
    min_value=2,
    max_value=10_000,
)
async def clock(ctx, period: int):
    await ctx.defer()
    if period > 10_000 or period <= 1:
        await ctx.respond(
            "Invalid argument for `period`: Must be an integer between 2 and 10,000.",
            ephemeral=True,
        )
        return
    save = generate.clock(period)
    file = saveToBytes(save)
    await ctx.respond("Here's your generated save!", file=file)


@bot.slash_command(description="Convert a message into uwu-speak")
async def uwuify(ctx, message: str):
    await ctx.defer()
    if len(message) == 0:
        await ctx.respond(
            "Invalid argument for `message`: Message must be at least 1 character long.",
            ephemeral=True,
        )
        return
    uwu = uwuify_string(message)
    await ctx.respond(uwu)


@bot.slash_command(description="See what time it is for skm")
async def skmtime(ctx):
    await ctx.defer()
    melbourne_time = datetime.now(melbourne_tz)
    formatted_time = melbourne_time.strftime("%I:%M %p")
    await ctx.respond(f"Current time for skm: {formatted_time}.")


@bot.slash_command(description="Find a random roblox game")
@option(
    "skipdefaultplace",
    description="Try to search for a game which isn't a default place (may take a while)",
    default=False,
    required=False,
)
@option(
    "maxattempts",
    description="Max number of search attempts when using skipdefaultplace",
    min_value=1,
    max_value=100,
    default=20,
    required=False,
)
async def randomgame(ctx, skipdefaultplace: bool, maxattempts: int):
    await ctx.defer()

    if skipdefaultplace == True:
        searching_message = await ctx.respond(
            "Searching for a game which isn't a default place, please wait... (this may take a while)",
        )
    else:
        searching_message = await ctx.respond("Searching, please wait...")

    search_attempts = 0
    found = False
    while found == False:
        search_attempts += 1
        if search_attempts >= maxattempts:
            await searching_message.edit(
                "Couldn't find a game which isn't a default place. Run the command again to try another search.",
            )
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://random-roblox-game.vercel.app/api/get-random?popular=no"
            ) as res:
                if res.status != 200:
                    await searching_message.edit(
                        "There was an error contacting `random-roblox-game.vercel.app`. Please try again in a few minutes.",
                    )
                    return
                resJson = await res.json()
                name = resJson["name"]
                description = resJson["desc"]
                creatorName = resJson["creator"]["name"]

        if skipdefaultplace == True:
            if (creatorName.lower() in name.lower()) or (
                description and "roblox studio" in description.lower()
            ):
                await searching_message.edit(
                    f"Searching for a game which isn't a default place, please wait... (this may take a while) [{search_attempts}/{maxattempts}]"
                )
                await asyncio.sleep(1)
                continue
            else:
                found = True
        found = True

    creatorId = resJson["creator"]["id"]
    image = resJson["image"]
    placeId = resJson["placeId"]
    timestamp = resJson["updated"].replace("Z", "")
    timestamp = timestamp.split(".")[0] + "." + timestamp.split(".")[1].ljust(3, "0")

    check_count = 0
    pending = True
    while pending:
        check_count += 1
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={creatorId}&size=420x420&format=Png&isCircular=false"
            ) as headshot_req:
                headshot_json = await headshot_req.json()
                if check_count >= 5:
                    break
                if headshot_json["data"][0]["state"] == "Completed":
                    pending = False
                    break
                await asyncio.sleep(1)

    if pending == False:
        headshot_url = headshot_json["data"][0]["imageUrl"]
    else:
        headshot_url = ""

    embed = (
        discord.Embed(
            url=f"https://www.roblox.com/games/{placeId}",
            title=name,
            description=description,
            timestamp=datetime.fromisoformat(timestamp),
        )
        .set_author(
            name=creatorName,
            url=f"https://www.roblox.com/users/{creatorId}",
            icon_url=headshot_url,
        )
        .set_thumbnail(url=image)
        .set_footer(
            text="Last updated",
        )
    )

    await searching_message.edit("Random roblox game:", embed=embed)


@generateCommand.command(
    description="A counter that counts up or down within a specific range."
)
@option(
    "min",
    description="Minimum value, the counter will reset to this.",
    min_value=0,
    max_value=99_999,
)
@option(
    "max",
    description="Maximum value, this is the highest number the counter will count to.",
    min_value=1,
    max_value=100_000,
)
@option(
    "direction",
    description="Whether to count up or down, or both.",
    choices=["up", "down", "up/down"],
)
async def counter(ctx, min: int, max: int, direction: str):
    await ctx.defer()
    if min >= max:
        await ctx.respond(
            "Invalid arguments: `max` must be greater than `min`.", ephemeral=True
        )
        return
    if direction == "up":
        dir = 1
    elif direction == "down":
        dir = -1
    elif direction == "up/down":
        dir = 0
    else:
        await ctx.respond("Invalid argument for `direction`.", ephemeral=True)
        return
    save = generate.counter(min, max, dir)
    file = saveToBytes(save)
    await ctx.respond("Here's your generated save!", file=file)


@generateCommand.command(description="Convert an image into a save.")
@option("image", discord.Attachment, description="The image to convert.")
@option(
    "size",
    description="The size of the longest dimension.",
    min_value=1,
    max_value=1_000,
    default=100,
    required=False,
)
@option(
    "transparency",
    description="Whether to enable transparency for the generated image.",
    default=True,
    required=False,
)
async def image(ctx, image: discord.Attachment, size: int, transparency: bool):
    await ctx.defer()
    imBytes = await image.read()
    im = Image.open(io.BytesIO(imBytes))
    save = generate.image(im, size, transparency)
    file = saveToBytes(save)
    await ctx.respond("Here's your generated save!", file=file)


@bot.event
async def on_message(message):
    totalStart = time.time()
    if message.author == bot.user:
        return

    if (
        (
            str(message.author.id) == "844957879714840597"
            and str(message.channel.id) == "1187662902610636910"
            and str(message.guild.id) == "956406294263242792"
        )
        or (
            str(message.author.id) == "665724183094755359"
            and str(message.channel.id) == "1220285303479337031"
            and str(message.guild.id) == "869012824620417075"
        )
    ) and any(
        attachment.width != None
        or attachment.height != None
        or attachment.content_type.startswith("video/")
        for attachment in message.attachments
    ):
        if re.search(r"me \w+ who", message.content):
            await message.reply("literally us")
        else:
            await message.reply("literally me")
        return

    linkRegex = (
        r"(https?:\/\/(www\.)?"
        r"(dpaste\.org/([-a-zA-Z0-9]*)(\/raw)?"
        r"|pastebin\.com(\/raw)?\/([-a-zA-Z0-9]*)"
        r"|dpaste\.com\/([-a-zA-Z0-9]*)))"
    )
    saveRegex = (
        r"(?<![\d\w,;?+])"  # Blocks
        r"(?>"
        r"(?<b>"
        r"\d+,"
        r"[01]?"
        r"(?>,(?<d>-?\d*\.?\d*)){3}"
        r"(?>(\+|,)(?&d)(?!,))*"
        r";?"
        r")+"
        r"(?<!;)\?"
        r")"
        r"(?>"  # Connections
        r"(?<i>[1-9][0-9]*),"
        r"(?&i)"
        r";?"
        r")*"
        r"(?<!;)\?"
        r"(?>"  # Buildings
        r"[A-Za-z]+,"
        r"(?>(?&d),){3}"
        r"(?>(?&d),){9}"
        r"(?>[01](?&i),?)*"
        r"(?<!,)"
        r";?"
        r")*"
        r"(?<!;)\?"
        r"("  # Sign data
        r"([0-9a-fA-F]{2})"
        r")*"
        r"(?![\d\w,;?+])"
    )

    maxSize = 500000

    messageHasLink = re.search(linkRegex, message.content)
    if messageHasLink:
        try:
            url = messageHasLink.group(0)
            if "/raw" not in url and ".txt" not in url:
                if "dpaste.org" in url:
                    url += "/raw"
                elif "dpaste.com" in url:
                    url += ".txt"
                else:  # pastebin
                    url = url.split("com/")[0] + "com/raw/" + url.split("com/")[1]
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    saveString = await response.text()
            if len(saveString) > maxSize:
                await message.reply(
                    f"Sorry, I can't render a preview for that save, it's over {maxSize//1000} KiB!",
                    mention_author=False,
                )
                return

            renderingMessage = await message.reply(
                "Rendering save...", mention_author=False
            )

            print(saveString)

            renderStart = time.time()
            renderTask = asyncio.create_task(
                render(saveString, message.id, renderingMessage)
            )
            success, renderedImage, save = await renderTask
            if not success:
                await renderingMessage.edit(
                    f"Sorry, I couldn't render a preview for that save! The render took longer than 120 seconds."
                )
                return
            renderTime = round((time.time() - renderStart) * 1000, 1)
            previewFile = discord.File(fp=renderedImage, filename="preview.gif")
            embed = discord.Embed(title="Save info")
            embed.add_field(name="Blocks", value=save.blockCount, inline=True)
            embed.add_field(name="Connections", value=save.connectionCount, inline=True)
            embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
            embed.add_field(name="Link", value=url)
            embed.set_image(url="attachment://preview.gif")

            totalTime = round((time.time() - totalStart) * 1000, 1)
            embed.set_footer(
                text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms."
            )

            await renderingMessage.edit(
                "Here's a preview of that save!",
                file=previewFile,
                embed=embed,
            )
            os.remove(renderedImage)
        except Exception as e:
            print(
                f"An error occured while uploading to dpaste: {traceback.format_exc()}: {e}"
            )
            await message.reply(
                f"Sorry, I couldn't render a preview for that save! Here's the error: {e}\n\n{traceback.format_exc()}"
            )
    else:
        messageHasSave = re.search(saveRegex, message.content)
        if messageHasSave:
            saveString = messageHasSave.group(0)
            if len(saveString) > maxSize:
                await message.reply(
                    f"Sorry, I couldn't render a preview for that save, it's over {maxSize//1000} KiB!",
                    mention_author=False,
                )
                return
            data = {"content": saveString, "syntax": "text", "expiry_days": 365}

            renderingMessage = await message.reply(
                "Rendering save...", mention_author=False
            )
            try:
                res = requests.post(
                    "https://dpaste.com/api/v2/", data=data, headers=DPASTE_HEADERS
                )
                res.raise_for_status()
                url = res.text.rstrip("\n") + ".txt"
                expiry = round(time.time() + (60 * 60 * 24 * 365))  # one year from now
                expiryTimestamp = f"<t:{expiry}:R>"

                renderStart = time.time()
                renderTask = asyncio.create_task(
                    render(saveString, message.id, renderingMessage)
                )
                success, renderedImage, save = await renderTask
                if not success:
                    await renderingMessage.edit(
                        f"Sorry, I couldn't render a preview for that save! The render took longer than 120 seconds."
                    )
                    return
                renderTime = round((time.time() - renderStart) * 1000, 1)
                previewFile = discord.File(fp=renderedImage, filename="preview.gif")
                embed = discord.Embed(title="Save info")
                embed.add_field(name="Blocks", value=save.blockCount, inline=True)
                embed.add_field(
                    name="Connections", value=save.connectionCount, inline=True
                )
                embed.add_field(
                    name="Raw size", value=str(len(saveString)), inline=True
                )
                embed.add_field(name=f"Link (expires {expiryTimestamp})", value=url)
                embed.set_image(url="attachment://preview.gif")

                totalTime = round((time.time() - totalStart) * 1000, 1)
                embed.set_footer(
                    text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms."
                )

                await renderingMessage.edit(
                    f"Here's a preview of that save!",
                    file=previewFile,
                    embed=embed,
                )
                os.remove(renderedImage)
            except Exception as e:
                print(
                    f"An error occured while uploading to dpaste: {traceback.format_exc()}: {e}"
                )
                await message.reply(
                    f"Sorry, I couldn't render a preview for that save! Here's the error: {e}\n\n{traceback.format_exc()}"
                )
        elif len(message.attachments) > 0:
            file = message.attachments[0]
            if message.attachments[0].content_type == "video/x-ms-wmv": # Check if it's a roblox recording that needs to be re-encoded
                if file.size > 8_000_000: # max 8mb
                    return
                print("VIDEO TO TRANSCODE FOUND!!!!!")
                await message.attachments[0].save("video_to_transcode.wmv")
                i = ffmpeg.input("video_to_transcode.wmv")
                ffmpeg.output(
                    i,
                    "transcoded_video.mp4",
                ).overwrite_output().run()
                file = discord.File(fp="transcoded_video.mp4", filename="transcoded.mp4")
                await message.reply("Looks like you sent a video file which won't play correctly in discord!\nI've transcoded it so it plays correctly:", file=file)
                return

            if file.size > maxSize:
                return
            fileBytes = await message.attachments[0].read()
            try:
                fileString = fileBytes.decode()
            except UnicodeDecodeError:
                return
            if re.match(saveRegex, fileString):
                saveString = fileString
                data = {"content": saveString, "syntax": "text", "expiry_days": 365}

                renderingMessage = await message.reply(
                    "Rendering save...", mention_author=False
                )
                try:
                    res = requests.post(
                        "https://dpaste.com/api/v2/", data=data, headers=DPASTE_HEADERS
                    )
                    res.raise_for_status()
                    url = res.text.rstrip("\n") + ".txt"
                    expiry = round(
                        time.time() + (60 * 60 * 24 * 365)
                    )  # one year from now
                    expiryTimestamp = f"<t:{expiry}:R>"

                    renderStart = time.time()
                    renderTask = asyncio.create_task(
                        render(saveString, message.id, renderingMessage)
                    )
                    success, renderedImage, save = await renderTask
                    if not success:
                        await renderingMessage.edit(
                            f"Sorry, I couldn't render a preview for that save! The render took longer than 120 seconds."
                        )
                        return
                    renderTime = round((time.time() - renderStart) * 1000, 1)
                    previewFile = discord.File(fp=renderedImage, filename="preview.gif")
                    embed = discord.Embed(title="Save info")
                    embed.add_field(name="Blocks", value=save.blockCount, inline=True)
                    embed.add_field(
                        name="Connections", value=save.connectionCount, inline=True
                    )
                    embed.add_field(
                        name="Raw size", value=str(len(saveString)), inline=True
                    )
                    embed.add_field(name=f"Link (expires {expiryTimestamp})", value=url)
                    embed.set_image(url="attachment://preview.gif")

                    totalTime = round((time.time() - totalStart) * 1000, 1)
                    embed.set_footer(
                        text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms."
                    )

                    await renderingMessage.edit(
                        f"Here's a preview of that save!",
                        file=previewFile,
                        embed=embed,
                    )
                    os.remove(renderedImage)
                except Exception as e:
                    print(
                        f"An error occured while uploading to dpaste: {traceback.format_exc()}: {e}"
                    )
                    await message.reply(
                        f"Sorry, I couldn't render a preview for that save! Here's the error: {e}\n\n{traceback.format_exc()}"
                    )

# thanks https://stackoverflow.com/a/64439347
def compress_video(video_full_path, output_file_name, target_size):

    # Reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000

    probe = ffmpeg.probe(video_full_path)
    # Video duration, in s.
    duration = float(probe["format"]["duration"])
    # Audio bitrate, in bps.
    audio_bitrate = float(
        next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)[
            "bit_rate"
        ]
    )
    # Target total bitrate, in bps.
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    # Target audio bitrate, in bps
    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
        if audio_bitrate < min_audio_bitrate < target_total_bitrate:
            audio_bitrate = min_audio_bitrate
        elif audio_bitrate > max_audio_bitrate:
            audio_bitrate = max_audio_bitrate
    # Target video bitrate, in bps.
    video_bitrate = target_total_bitrate - audio_bitrate

    i = ffmpeg.input(video_full_path)
    ffmpeg.output(
        i, os.devnull, **{"c:v": "libx264", "b:v": video_bitrate, "pass": 1, "f": "mp4"}
    ).overwrite_output().run()
    ffmpeg.output(
        i,
        output_file_name,
        **{
            "c:v": "libx264",
            "b:v": video_bitrate,
            "pass": 2,
            "c:a": "aac",
            "b:a": audio_bitrate,
        },
    ).overwrite_output().run()


async def check_rss_feed():
    await bot.wait_until_ready()
    while True:
        for channel in youtube_channels:
            rss_feed_url = (
                f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
            )
            if not os.path.exists("sentvideos.txt"):
                open("sentvideos.txt", "w")
            with open("sentvideos.txt", "r") as f:
                sent_videos = f.read().split("\n")
            try:
                feed = feedparser.parse(rss_feed_url)
                latest = feed.entries[0]
                latest_link = latest.link
                if latest_link not in sent_videos:
                    print("NEW VIDEO")
                    print(latest_link)

                    streams = YouTube(
                        latest_link, use_oauth=True, allow_oauth_cache=True
                    ).streams
                    try:
                        streams.filter(
                            type="video", adaptive=True, res="720p"
                        ).first().download(filename="video")
                    except:
                        streams.filter(type="video", adaptive=True).first().download(
                            filename="video"
                        )
                    YouTube(
                        latest_link, use_oauth=True, allow_oauth_cache=True
                    ).streams.filter(only_audio=True).last().download(filename="audio")
                    # input_video = ffmpeg.input("video")
                    # input_audio = ffmpeg.input("audio")
                    # ffmpeg.concat(input_video, input_audio, v=1, a=1).output(
                    #     "output.mp4"
                    # ).overwrite_output().run()

                    subprocess.run(
                        "ffmpeg -y -i video -i audio -acodec copy -vcodec copy output.mp4",
                        shell=True,
                    )

                    if os.path.getsize("output.mp4") > 10_000_000:
                        compress_video(
                            os.path.join(os.getcwd(), "output.mp4"),
                            "output_compressed.mp4",
                            10_000,
                        )
                        file_to_upload = "output_compressed.mp4"
                    else:
                        file_to_upload = "output.mp4"

                    file = discord.File(fp=file_to_upload, filename="video.mp4")
                    channel = bot.get_channel(1187659525248004210)
                    await channel.send("", file=file)

                    with open("sentvideos.txt", "a") as f:
                        f.write(latest_link + "\n")

            except Exception as e:
                print("Error occurred:", e)

        await asyncio.sleep(60)


def main():
    # bot.loop.create_task(check_rss_feed())
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
