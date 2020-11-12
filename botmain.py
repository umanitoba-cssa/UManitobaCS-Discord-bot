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

#permission check function
def hasPermission(ctx,level):
    user = ctx.message.author
    if(level is "admin"):
        admin = discord.utils.get(ctx.message.guild.roles, name=adminRole)
        if admin in user.roles:
            return True 
        else:
            return False
    elif(level is "registered"):
        roles = []
        #add every allowed role to 'roles'
        for role in defaultRoles:
            #convert the strings into actual role objects
            roles.append(discord.utils.get(ctx.message.guild.roles, name=role))
        for role in execRoles:
            roles.append(discord.utils.get(ctx.message.guild.roles, name=role))
        roles.append(discord.utils.get(ctx.message.guild.roles, name=adminRole))
        for role in roles:
            if role in user.roles:
                return True 
        return False

#Start bot
bot = commands.Bot(command_prefix=PREFIX)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    #guild = discord.utils.get(client.guilds, name=GUILD)

#default format for commands, where the function name is the command to type
@bot.command()
@commands.has_role('admin')
async def test(ctx, *args):
    #send the arguments of the command back to the user
    await ctx.send(' '.join(args))

@bot.command()
async def colour(ctx, *args):

    #check if this colour is NOT in colour roles
    def checkColours(colour):
        for i in colourRoles:
            if(i is colour):
                return False
        return True

    if(len(args) == 0):
        await ctx.send("Error: A colour must be specificed.")
        return
    
    if(args[0] == 'add' and hasPermission(ctx,"admin")):
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

    elif(args[0] == 'delete' and hasPermission(ctx,"admin")):
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
                    await ctx.send("Colour role `" + args[1].lower() + "` deleted.")

                except discord.Forbidden:
                    await bot.say("Error: Missing Permissions to delete this role.")

            else:
                await ctx.send("Error: Colour role `" + args[1] + "` not found.")
        else:
            await ctx.send("Error: Correct format is: `" + PREFIX + "colour delete {{colour}}`")
    
    elif hasPermission(ctx,"registered"):
        #set or remove colour role of user
        user = ctx.message.author

        role = discord.Role
        roleFound = False
        for i in colourRoles:
            if discord.utils.get(ctx.message.guild.roles, name=i) in user.roles:
                role = discord.utils.get(ctx.message.guild.roles, name=i)
                roleFound = True
                break

        if(args[0] == 'remove'):
            #remove colour role, check which one they have then remove it 
            if(roleFound):
                await user.remove_roles(role)
                await ctx.send("Colour role `" + role.name + "` removed.")
            else:
                await ctx.send("Error: No colour role to remove.")

        else:
            #check if the given colour is valid
            validColour = False
            for i in colourRoles:
                if i == args[0]:
                    validColour = True
                    break

            if validColour:
                if(roleFound):
                    await user.remove_roles(role)
                
                newRole = discord.utils.get(ctx.message.guild.roles, name=args[0])
                await user.add_roles(newRole)
                await ctx.send("Colour role `" + newRole.name + "` set.")
            else:
                await ctx.send("Error: Colour role `" + args[0] + "` not found.")
    else:
        await ctx.send("Error: You do not have permission to use this command.")


@bot.command()
async def setyear(ctx, *args):
    user = ctx.message.author

    def checkUserYear(year):
        if discord.utils.get(ctx.message.guild.roles, name=year) in user.roles:
            return True
        else:
            return False

    if(hasPermission(ctx,"registered")):
        if(len(args) == 1):
            year = args[0].lower().capitalize() + " Year"

            if(year in ['First Year', 'Second Year', 'Third Year', 'Fourth Year']):
                if(checkUserYear(year)):
                    await ctx.send("Error: You already have the `" + year + "` role.")
                else:
                    await user.add_roles(discord.utils.get(ctx.message.guild.roles, name=year))
                    await ctx.send("`" + year + "` role added.")
            else:
                await ctx.send("Error: Year must be first, second, third, or fourth.")
        else:
            await ctx.send("Error: correct format is `" + PREFIX + "setyear {{year}}`")
    else:
        await ctx.send("Error: You do not have permission to use this command.")


@bot.command()
async def removeyear(ctx, *args):
    user = ctx.message.author

    if(hasPermission(ctx,"registered")):
        if(len(args) == 1):
            year = args[0].lower().capitalize() + " Year"

            role = discord.utils.get(ctx.message.guild.roles, name=year)
            
            if role in user.roles:
                await user.remove_roles(role)
                await ctx.send("Year role `" + role.name + "` removed.")
            else:
                if(args[0] == 'all'):
                    for year in ['First Year', 'Second Year', 'Third Year', 'Fourth Year']:
                        role = discord.utils.get(ctx.message.guild.roles, name=year)
                        if role in user.roles:
                            await user.remove_roles(role)
                            await ctx.send("Year role `" + role.name + "` removed.")
                else:
                    await ctx.send("Error: Year role for `" + args[0] + "` was not found.")

        else:
            await ctx.send("Error: correct format is `" + PREFIX + "setyear {{year}}`")
    else:
        await ctx.send("Error: You do not have permission to use this command.")


bot.run(TOKEN)

