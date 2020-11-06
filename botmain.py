import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
PREFIX = '.'


#client = discord.Client()
bot = commands.Bot(command_prefix=PREFIX)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    #guild = discord.utils.get(client.guilds, name=GUILD)

#default format for commands, where the function name is the command to type
@bot.command()
async def test(ctx, *args):
    await ctx.send(' '.join(args))


bot.run(TOKEN)

