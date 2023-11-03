from render import render
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
from PIL import Image

load_dotenv()

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.all()

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print('-----')
    game = discord.Game("Circuit Maker 2")
    await bot.change_presence(activity=game)

@bot.slash_command(description="Get the UserId for a roblox username.")
async def getuser(ctx, username: str):
    userUrl = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    res = requests.post(userUrl, json=payload)
    resJson = res.json()
    userId = resJson["data"][0]["id"]
    await ctx.respond(str(userId), ephemeral=True)

def saveToBytes(save):
    saveString = save.exportSave()
    file = discord.File(io.BytesIO(saveString.encode()),filename=f"generated.txt")
    return file

generateCommand = bot.create_group("generate", "Automatically generate circuits from parameters.")

@generateCommand.command(description="A clock with a given period.")
@option(
    "period",
    description="The period of the clock, in ticks/cycle.",
    min_value=2,
    max_value=10_000
)
async def clock(ctx, period: int):
    if period > 10_000 or period <= 1:
        await ctx.respond("Invalid argument for `period`: Must be an integer between 2 and 10,000.", ephemeral=True)
        return
    save = generate.clock(period)
    file = saveToBytes(save)
    await ctx.respond("Here's your generated save!", file=file)

@generateCommand.command(description="A counter that counts up or down within a specific range.")
@option(
    "min",
    description="Minimum value, the counter will reset to this.",
    min_value=0,
    max_value=99_999
)
@option(
    "max",
    description="Maximum value, this is the highest number the counter will count to.",
    min_value=1,
    max_value=100_000
)
@option("direction", description="Whether to count up or down, or both.", choices=["up", "down", "up/down"])
async def counter(ctx, min: int, max: int, direction: str):
    if min >= max:
        await ctx.respond("Invalid arguments: `max` must be greater than `min`.", ephemeral=True)
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
@option(
    "image",
    discord.Attachment,
    description="The image to convert."
)
@option(
    "size",
    description="The size of the longest dimension.",
    min_value=1,
    max_value=1_000,
    default=1,
    required=False
)
async def image(ctx, image: discord.Attachment, size: int):
    imBytes = await image.read()
    im = Image.open(io.BytesIO(imBytes))
    save = generate.image(im, size)
    file = saveToBytes(save)
    await ctx.respond("Here's your generated save!", file=file)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    linkRegex = r"(https?:\/\/(www\.)?(dpaste\.org/([-a-zA-Z0-9]*)(\/raw)?|pastebin\.com(\/raw)?\/([-a-zA-Z0-9]*)))"
    saveRegex = (
        "(?<![\d\w,;?+])" # Blocks
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

        "(?>" # Connections
          "(?<i>[1-9][0-9]*),"
          "(?&i)"
          ";?"
        ")*"
        "(?<!;)\?"

        "(?>" # Buildings
          "[A-Za-z]+,"
          "(?>(?&d),){3}"
          "(?>(?&d),){9}"
          "(?>[01](?&i),?)*"
          "(?<!,)"
          ";?"
        ")*"
        "(?<!;)\?"

        "(" # Sign data
          "([0-9a-fA-F]{2})"
        ")*"
        "(?![\d\w,;?+])"
    )

    maxSize = 3000000

    messageHasLink = re.search(linkRegex, message.content)
    if messageHasLink:
        totalStart = time.time()
        try:
            url = messageHasLink.group(0)
            if "/raw" not in url:
                if "dpaste.org" in url:
                    url += "/raw"
                else: # pastebin
                    url = url.split("com/")[0] + "com/raw/" + url.split("com/")[1]
            saveString = requests.get(url).text
            if len(saveString) > maxSize:
                await message.reply(f"Sorry, I can't render a preview for that save, it's over {maxSize//1000} KiB!", mention_author=False)
                return

            renderingMessage = await message.reply("Rendering save...", mention_author=False)
            
            renderStart = time.time()
            renderedImage, save = await render(saveString, message.id)
            renderTime = round((time.time() - renderStart) * 1000, 1)
            previewFile = discord.File(fp=renderedImage, filename="preview.gif")
            embed = discord.Embed(title="Save info")
            embed.add_field(name="Blocks", value=save.blockCount, inline=True)
            embed.add_field(name="Connections", value=save.connectionCount, inline=True)
            embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
            embed.add_field(name="Link", value=url)
            embed.set_image(url="attachment://preview.gif")

            totalTime = round((time.time() - totalStart) * 1000, 1)
            embed.set_footer(text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms.")

            await renderingMessage.delete()
            await message.reply("Here's a preview of that save!", file=previewFile, embed=embed, mention_author=False)
            os.remove(renderedImage)
        except Exception as e:
            print(f"An error occured while uploading to dpaste: {traceback.format_exc()}: {e}")
            await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}\n\n{traceback.format_exc()}")
    else:
        messageHasSave = re.search(saveRegex, message.content)
        if messageHasSave:
            totalStart = time.time()
            saveString = messageHasSave.group(0)
            if len(saveString) > maxSize:
                await message.reply(f"Sorry, I couldn't render a preview for that save, it's over {maxSize//1000} KiB!", mention_author=False)
                return
            headers = {"User-Agent": "Mozilla/5.0"}
            payload = {"lexer": "_text", "format": "url", "content": saveString}
            try:
                res = requests.post("https://dpaste.org/api/", headers=headers, data=payload)
                res.raise_for_status()
                url = res.text.rstrip("\n") + "/raw"
    
                renderingMessage = await message.reply("Rendering save...", mention_author=False)
    
                renderStart = time.time()
                renderedImage, save =  await render(saveString, message.id)
                renderTime = round((time.time() - renderStart) * 1000, 1)
                previewFile = discord.File(fp=renderedImage, filename="preview.gif")
                embed = discord.Embed(title="Save info")
                embed.add_field(name="Blocks", value=save.blockCount, inline=True)
                embed.add_field(name="Connections", value=save.connectionCount, inline=True)
                embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
                embed.add_field(name="Link", value=url)
                embed.set_image(url="attachment://preview.gif")
    
                totalTime = round((time.time() - totalStart) * 1000, 1)
                embed.set_footer(text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms.")
    
                await renderingMessage.delete()
                await message.reply(f"Here's a preview of that save!", file=previewFile, embed=embed, mention_author=False)
                os.remove(renderedImage)
            except Exception as e:
                print(f"An error occured while uploading to dpaste: {traceback.format_exc()}: {e}")
                await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}\n\n{traceback.format_exc()}")
        elif len(message.attachments) > 0:
            file = message.attachments[0]
            if file.size > maxSize:
                return
            fileBytes = await message.attachments[0].read()
            fileString = fileBytes.decode()
            if re.match(saveRegex, fileString):
                totalStart = time.time()
                saveString = fileString
                headers = {"User-Agent": "Mozilla/5.0"}
                payload = {"lexer": "_text", "format": "url", "content": saveString}
    
                renderingMessage = await message.reply("Rendering save...", mention_author=False)
                try:
                    res = requests.post("https://dpaste.org/api/", headers=headers, data=payload)
                    res.raise_for_status()
                    url = res.text.rstrip("\n") + "/raw"
    
                    renderStart = time.time()
                    renderedImage, save = await render(saveString, message.id)
                    renderTime = round((time.time() - renderStart) * 1000, 1)
                    previewFile = discord.File(fp=renderedImage, filename="preview.gif")
                    embed = discord.Embed(title="Save info")
                    embed.add_field(name="Blocks", value=save.blockCount, inline=True)
                    embed.add_field(name="Connections", value=save.connectionCount, inline=True)
                    embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
                    embed.add_field(name="Link", value=url)
                    embed.set_image(url="attachment://preview.gif")
    
                    totalTime = round((time.time() - totalStart) * 1000, 1)
                    embed.set_footer(text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms.")
    
                    await renderingMessage.delete()
                    await message.reply(f"Here's a preview of that save!", file=previewFile, embed=embed, mention_author=False)
                    os.remove(renderedImage)
                except Exception as e:
                    print(f"An error occured while uploading to dpaste: {traceback.format_exc()}: {e}")
                    await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}\n\n{traceback.format_exc()}")

bot.run(TOKEN)
