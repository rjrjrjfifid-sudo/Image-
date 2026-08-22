import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
VERCEL_URL = os.getenv("VERCEL_URL")  # Set this in Railway env

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.strip() == "$Gen":
        link = f"{VERCEL_URL}/tic-tac-toe"
        embed = discord.Embed(
            title="🖼️ Tic‑Tac‑Toe Image",
            description=f"Click the link to view the image:\n{link}",
            color=0x00ff00
        )
        embed.set_image(url=link)
        await message.channel.send(embed=embed)
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
