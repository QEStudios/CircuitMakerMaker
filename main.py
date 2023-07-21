from render import render
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import re
import requests
import time
import asyncio


load_dotenv()

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print('-----')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    linkRegex = r"(https?:\/\/(www\.)?(dpaste\.org/([-a-zA-Z0-9]*)\/raw|pastebin\.com\/raw\/([-a-zA-Z0-9]*)))"
    saveRegex = (
    # Match all blocks
    r"(((\d+,){2}(-?\d+(\.\d+)?,){3}(((\d+(\.\d+)?\+)*(\d+(\.\d+)?)))?;)*"
    r"((\d+,){2}(-?\d+(\.\d+)?,){3}(((\d+(\.\d+)?\+)*(\d+(\.\d+)?)))?\?)"
    # Match all connections
    r"((([1-9][0-9]*),([1-9][0-9]*)|((([1-9][0-9]*),([1-9][0-9]*);)+"
    r"([1-9][0-9]*),([1-9][0-9]*)))?\?)"
    # Match custom build syntax
    r"((\w+(,(-?\d+(\.\d+)?(\+-?\d+(\.\d+)?)*)*)+)(;(\w+(,(-?\d+(\.\d+)?(\+-?\d+(\.\d+)?)*)*)+))*)*\?"
    # Match sign data
    r"[0-9a-f]*(;[0-9a-fA-F]*)*)"
)
    maxSize = 500000
    
    if re.search(linkRegex, message.content):
        totalStart = time.time()
        try:
            url = re.search(linkRegex, message.content).group(0)
            saveString = requests.get(url).text
            if len(saveString) > maxSize:
                await message.reply(f"Sorry, I couldn't render a preview for that save, it's over {maxSize//1000} KiB!", mention_author=False)
                return
            renderStart = time.time()
            renderedImage, save = await render(saveString)
            renderTime = round((time.time() - renderStart) * 1000, 1)
            previewFile = discord.File(fp=renderedImage, filename="preview.gif")
            embed = discord.Embed(title="Save info")
            embed.add_field(name="Blocks", value=str(len(save.blocks)), inline=True)
            embed.add_field(name="Connections", value="\"ill add this later\" - skm", inline=True)
            embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
            embed.set_image(url="attachment://preview.gif")

            totalTime = round((time.time() - totalStart) * 1000, 1)
            embed.set_footer(text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms.")

            await message.reply("Here's a preview of that save!", file=previewFile, embed=embed, mention_author=False)
            renderedImage.close()
        except Exception as e:
            await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}")
    elif re.search(saveRegex, message.content):
        totalStart = time.time()
        saveString = re.search(saveRegex, message.content).group(0)
        if len(saveString) > maxSize:
            await message.reply(f"Sorry, I couldn't render a preview for that save, it's over {maxSize//1000} KiB!", mention_author=False)
            return
        headers = {"User-Agent": "Mozilla/5.0"}
        payload = {"lexer": "_text", "format": "url", "content": saveString}
        try:
            res = requests.post("https://dpaste.org/api/", headers=headers, data=payload)
            res.raise_for_status()
            url = res.text.rstrip("\n") + "/raw"

            renderStart = time.time()
            renderedImage, save =  await render(saveString)
            renderTime = round((time.time() - renderStart) * 1000, 1)
            previewFile = discord.File(fp=renderedImage, filename="preview.gif")
            embed = discord.Embed(title="Save info")
            embed.add_field(name="Blocks", value=str(len(save.blocks)), inline=True)
            embed.add_field(name="Connections", value="\"ill add this later\" - skm", inline=True)
            embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
            embed.set_image(url="attachment://preview.gif")

            totalTime = round((time.time() - totalStart) * 1000, 1)
            embed.set_footer(text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms.")

            await message.reply(f"Here's a dpaste link for that save: {url}\nAnd here's a preview of that save, too!", file=previewFile, embed=embed, mention_author=False)
        except Exception as e:
            print(f"An error occured while uploading to dpaste: {e}")
            await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}")
    elif len(message.attachments) > 0:
        fileBytes = await message.attachments[0].read()
        fileString = fileBytes.decode()
        if re.match(saveRegex, fileString):
            totalStart = time.time()
            saveString = fileString
            if len(saveString) > maxSize:
                await message.reply(f"Sorry, I couldn't render a preview for that save, it's over {maxSize//1000} KiB!", mention_author=False)
                return
            headers = {"User-Agent": "Mozilla/5.0"}
            payload = {"lexer": "_text", "format": "url", "content": saveString}
            try:
                res = requests.post("https://dpaste.org/api/", headers=headers, data=payload)
                res.raise_for_status()
                url = res.text.rstrip("\n") + "/raw"

                renderStart = time.time()
                renderedImage, save = await render(saveString)
                renderTime = round((time.time() - renderStart) * 1000, 1)
                previewFile = discord.File(fp=renderedImage, filename="preview.gif")
                embed = discord.Embed(title="Save info")
                embed.add_field(name="Blocks", value=str(len(save.blocks)), inline=True)
                embed.add_field(name="Connections", value="\"ill add this later\" - skm", inline=True)
                embed.add_field(name="Raw size", value=str(len(saveString)), inline=True)
                embed.set_image(url="attachment://preview.gif")

                totalTime = round((time.time() - totalStart) * 1000, 1)
                embed.set_footer(text=f"Preview took {renderTime} ms to render, total response time {totalTime} ms.")

                await message.reply(f"Here's a dpaste link for that save: {url}\nAnd here's a preview of that save, too!", file=previewFile, embed=embed, mention_author=False)
            except Exception as e:
                print(f"An error occured while uploading to dpaste: {e}")
                await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}")

bot.run(TOKEN)
