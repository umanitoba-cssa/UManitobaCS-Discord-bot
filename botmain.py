import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
PREFIX = '.'

#lists
colourRoles = []

#read in data (may change from txt file if issues come up)
coloursFile = open("colourRoles.txt","r")
for line in coloursFile:
    colourRoles.append(line)
coloursFile.close()

bot = commands.Bot(command_prefix=PREFIX)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    #guild = discord.utils.get(client.guilds, name=GUILD)

#default format for commands, where the function name is the command to type
@bot.command()
async def test(ctx, *args):
    #send the arguments of the command back to the user
    await ctx.send(' '.join(args))

@bot.command()
async def colour(ctx, *args):

    def checkColours(colour):
        for i in colourRoles:
            if(i == colour):
                return False
        return True
    
    if(args[0] == 'add'):
        # adding colours
        if(len(args) == 3):
            colour = args[1]
            if(checkColours(args[2].lower())):
                if(colour[0] == '#' and len(colour) == 7):
                    guild = ctx.guild
                    roleName = args[2].lower()
                    await guild.create_role(name=roleName,colour=discord.Colour(int(colour[1:], 16)))
                    await ctx.send("Colour role: " + roleName + " added.")

                    #add the new colour to our file, then add it to our list
                    coloursFile = open("colourRoles.txt", "a")
                    coloursFile.write("\n" + roleName)
                    coloursFile.close()
                    colourRoles.append(roleName)
                else:
                    await ctx.send("Error: Invalid hex input: " + colour)
            else:
                await ctx.send("Error: Colour role with that name already exists.")
        else: 
            await ctx.send("Error: Correct format is: " + PREFIX + "colour add #{{colour}} {{label}}")

    elif(args[0] == 'delete'):
        print()
    
    else:
        print()


bot.run(TOKEN)

