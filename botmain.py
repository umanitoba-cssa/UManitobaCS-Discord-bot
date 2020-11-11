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
defaultRoles = []
execRoles = []
adminRole = ""
yearRoles = []

#read in data (may change from txt file if issues come up)
coloursFile = open("colourRoles.txt","r")
colourRoles = coloursFile.read().split("\n")
coloursFile.close()

#read in default roles
roleFile = open("roles.txt","r")
line = roleFile.readline()

#the roles.txt file must be formatted in the order
# Default roles
# Exec roles
# Admin role
# Year roles
if(line[0] is "#"):
    line = roleFile.readline()
    while(line[0] is not "#"):
        defaultRoles.append(line.replace("\n",""))
        line = roleFile.readline()

if(line[0] is "#"):
    line = roleFile.readline()
    while(line[0] is not "#"):
        execRoles.append(line.replace("\n",""))
        line = roleFile.readline()

if(line[0] is "#"):
    line = roleFile.readline()
    adminRole = line.replace("\n","") 
    line = roleFile.readline()

if(line[0] is "#"):
    line = roleFile.readline()
    while(line and line[0] is not "#"):
        yearRoles.append(line.replace("\n",""))
        line = roleFile.readline()


#Start bot
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
            if(i is colour):
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
                    await ctx.send("Colour role: `" + roleName + "` added.")

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
            await ctx.send("Error: Correct format is: `" + PREFIX + "colour add #{{hexColour}} {{label}}`")

    elif(args[0] == 'delete'):
        #removing colours 
        if(len(args) == 2):
            role = discord.utils.get(ctx.message.guild.roles, name=args[1].lower())
            if(checkColours(args[1].lower()) and role):
                try:
                    await role.delete()
                    #colour exits, remove it
                    colourRoles.remove(args[1].lower())
                    #rewrite the file
                    coloursFile = open("colourRoles.txt", "w")
                    for i in colourRoles:
                        coloursFile.write("\n" + i)
                    coloursFile.close()
                    await ctx.send("Colour role `" + args[1].lower() + "` removed.")

                except discord.Forbidden:
                    await bot.say("Error: Missing Permissions to delete this role.")

            else:
                await ctx.send("Error: Colour role `" + args[1] + "` not found.")
        else:
            await ctx.send("Error: Correct format is: `" + PREFIX + "colour delete {{colour}}`")
    
    else:
        #set colour role of user

        if(len(args) == 0 or args[0] is "remove"):
            #remove colour role 
            print()
        elif(checkColours(args[0])):
            print()


bot.run(TOKEN)

