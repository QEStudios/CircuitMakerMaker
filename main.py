from render import render
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import traceback
import regex as re
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
    game = discord.Game("Circuit Maker 2")
    await bot.change_presence(activity=game)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    linkRegex = r"(https?:\/\/(www\.)?(dpaste\.org/([-a-zA-Z0-9]*)\/raw|pastebin\.com\/raw\/([-a-zA-Z0-9]*)))"
    saveRegex = ( # https://regex101.com/r/pTigOh/1
    # Match all blocks
    r"^((^|(?<!^);)((\d+,)(\d*,)((-?\d+(\.\d+)?)?,){3}(((\d+(\.\d+)?\+)*(\d+(\.\d+)?)))?))*\?"
    # Match all connections
    r"((([1-9][0-9]*),([1-9][0-9]*)|((([1-9][0-9]*),([1-9][0-9]*);)+"
    r"([1-9][0-9]*),([1-9][0-9]*)))?\?)"
    # Match custom build syntax
    r"((\w+(,(-?\d+(\.\d+)?(\+-?\d+(\.\d+)?)*)*)+)(;(\w+(,(-?\d+(\.\d+)?(\+-?\d+(\.\d+)?)*)*)+))*)*\?"
    # Match sign data
    r"[0-9a-fA-F]*(;[0-9a-fA-F]*)*"
)
    maxSize = 3000000

    messageHasLink = re.search(linkRegex, message.content)
    if messageHasLink:
        totalStart = time.time()
        try:
            url = messageHasLink.group(0)
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
            await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}")
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
                await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}")
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
                    await message.reply(f"Sorry, I couldn't render a preview for that save! Here's the error: {e}")

bot.run(TOKEN)
