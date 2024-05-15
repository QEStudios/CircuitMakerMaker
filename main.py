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
import time
import asyncio
import json
import threading
import feedparser
import ffmpeg
from pytube import YouTube
from PIL import Image

load_dotenv()

TOKEN = os.getenv("TOKEN")

DAYTELL_CHANNEL_ID = "UCvL2QwDXWFJn1J5aNjaUczw"

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
    res = requests.post(userUrl, json=payload)
    resJson = res.json()
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
    res = requests.get(
        "https://timeapi.io/api/Time/current/zone?timeZone=Australia/Melbourne"
    )
    if res.status_code != 200:
        await ctx.respond(
            "There was an error contacting `timeapi.io`. Please try again in a few minutes.",
            ephemeral=True,
        )
        return
    resJson = json.loads(res.text)
    modTime = resJson["time"]
    modTime = (int(modTime.split(":")[0]) - 1) % 12 + 1
    if int(resJson["time"].split(":")[0]) > 11:
        amPm = "PM"
    else:
        amPm = "AM"
    minutes = resJson["time"].split(":")[1]
    formatted_time = f"{modTime:02}:{minutes} {amPm}"
    await ctx.respond(f"Current time for skm: {formatted_time}.")


@bot.slash_command(description="Find a random roblox game")
async def randomgame(ctx):
    await ctx.defer()
    res = requests.get(
        "https://random-roblox-game.vercel.app/api/get-random?popular=no"
    )
    if res.status_code != 200:
        await ctx.respond(
            "There was an error contacting `random-roblox-game.vercel.app`. Please try again in a few minutes.",
            ephemeral=True,
        )
        return
    resJson = json.loads(res.text)
    name = resJson["name"]
    creatorName = resJson["creatorName"]
    description = resJson["desc"]
    image = resJson["image"]
    placeId = resJson["placeId"]
    await ctx.respond(
        f"Random roblox game:\n**{name}** by {creatorName}\n<https://www.roblox.com/games/{placeId}>"
    )


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
async def image(ctx, image: discord.Attachment, size: int):
    await ctx.defer()
    imBytes = await image.read()
    im = Image.open(io.BytesIO(imBytes))
    save = generate.image(im, size)
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

    linkRegex = r"(https?:\/\/(www\.)?(dpaste\.org/([-a-zA-Z0-9]*)(\/raw)?|pastebin\.com(\/raw)?\/([-a-zA-Z0-9]*)))"
    saveRegex = (
        "(?<![\d\w,;?+])"  # Blocks
        "(?>"
        "(?<b>"
        "\d+,"
        "[01]?"
        "(?>,(?<d>-?\d*\.?\d*)){3}"
        "(?>(\+|,)(?&d)(?!,))*"
        ";?"
        ")+"
        "(?<!;)\?"
        ")"
        "(?>"  # Connections
        "(?<i>[1-9][0-9]*),"
        "(?&i)"
        ";?"
        ")*"
        "(?<!;)\?"
        "(?>"  # Buildings
        "[A-Za-z]+,"
        "(?>(?&d),){3}"
        "(?>(?&d),){9}"
        "(?>[01](?&i),?)*"
        "(?<!,)"
        ";?"
        ")*"
        "(?<!;)\?"
        "("  # Sign data
        "([0-9a-fA-F]{2})"
        ")*"
        "(?![\d\w,;?+])"
    )

    maxSize = 500000

    messageHasLink = re.search(linkRegex, message.content)
    if messageHasLink:
        try:
            url = messageHasLink.group(0)
            if "/raw" not in url:
                if "dpaste.org" in url:
                    url += "/raw"
                else:  # pastebin
                    url = url.split("com/")[0] + "com/raw/" + url.split("com/")[1]
            saveString = requests.get(url).text
            if len(saveString) > maxSize:
                await message.reply(
                    f"Sorry, I can't render a preview for that save, it's over {maxSize//1000} KiB!",
                    mention_author=False,
                )
                return

            renderingMessage = await message.reply(
                "Rendering save...", mention_author=False
            )

            renderStart = time.time()
            renderTask = asyncio.create_task(render(saveString, message.id))
            success, renderedImage, save = await renderTask
            if not success:
                await message.reply(
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

            await renderingMessage.delete()
            await message.reply(
                "Here's a preview of that save!",
                file=previewFile,
                embed=embed,
                mention_author=False,
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
            headers = {"User-Agent": "Mozilla/5.0"}
            payload = {"lexer": "_text", "format": "url", "content": saveString}

            renderingMessage = await message.reply(
                "Rendering save...", mention_author=False
            )
            try:
                res = requests.post(
                    "https://dpaste.org/api/", headers=headers, data=payload
                )
                res.raise_for_status()
                url = res.text.rstrip("\n") + "/raw"

                renderStart = time.time()
                renderTask = asyncio.create_task(render(saveString, message.id))
                success, renderedImage, save = await renderTask
                if not success:
                    await message.reply(
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
                embed.add_field(name="Link", value=url)
                embed.set_image(url="attachment://preview.gif")

                totalTime = round((time.time() - totalStart) * 1000, 1)
                embed.set_footer(
                    text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms."
                )

                await renderingMessage.delete()
                await message.reply(
                    f"Here's a preview of that save!",
                    file=previewFile,
                    embed=embed,
                    mention_author=False,
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
            if file.size > maxSize:
                return
            fileBytes = await message.attachments[0].read()
            fileString = fileBytes.decode()
            if re.match(saveRegex, fileString):
                saveString = fileString
                headers = {"User-Agent": "Mozilla/5.0"}
                payload = {"lexer": "_text", "format": "url", "content": saveString}

                renderingMessage = await message.reply(
                    "Rendering save...", mention_author=False
                )
                try:
                    res = requests.post(
                        "https://dpaste.org/api/", headers=headers, data=payload
                    )
                    res.raise_for_status()
                    url = res.text.rstrip("\n") + "/raw"

                    renderStart = time.time()
                    renderTask = asyncio.create_task(render(saveString, message.id))
                    success, renderedImage, save = await renderTask
                    if not success:
                        await message.reply(
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
                    embed.add_field(name="Link", value=url)
                    embed.set_image(url="attachment://preview.gif")

                    totalTime = round((time.time() - totalStart) * 1000, 1)
                    embed.set_footer(
                        text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms."
                    )

                    await renderingMessage.delete()
                    await message.reply(
                        f"Here's a preview of that save!",
                        file=previewFile,
                        embed=embed,
                        mention_author=False,
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
        rss_feed_url = (
            f"https://www.youtube.com/feeds/videos.xml?channel_id={DAYTELL_CHANNEL_ID}"
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

                YouTube(latest_link).streams.filter(
                    progressive=True, file_extension="mp4"
                ).order_by("resolution").desc().first().download(filename="daytell.mp4")
                if os.path.getsize("daytell.mp4") > 10_000_000:
                    compress_video(
                        os.path.join(os.getcwd(), "daytell.mp4"),
                        "daytell_compressed.mp4",
                        10_000,
                    )
                    file_to_upload = "daytell_compressed.mp4"
                else:
                    file_to_upload = "daytell.mp4"

                file = discord.File(fp=file_to_upload, filename="video.mp4")
                channel = bot.get_channel(869012824620417078)
                await channel.send("", file=file)

                with open("sentvideos.txt", "a") as f:
                    f.write(latest_link + "\n")

        except Exception as e:
            print("Error occurred:", e)

        await asyncio.sleep(1)


def main():
    bot.loop.create_task(check_rss_feed())
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
