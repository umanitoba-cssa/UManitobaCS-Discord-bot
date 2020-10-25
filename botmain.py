import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
PREFIX = "."


client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    #guild = discord.utils.get(client.guilds, name=GUILD)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content[0] == PREFIX:
        msg = message.content[1:]
        if msg == "form":
            await message.channel.send("Command received!")
        elif msg.split()[0] == "colour":
            await message.channel.send("Command 2 received!")


client.run(TOKEN)

