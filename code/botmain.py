# Custom Discord bot for the University of Manitoba Computer Science Discord server
# Made by Colton Dietterle (2021)
#
# If you've been put charge of maintaining this and have any questions, send an email to
# cdietterle306@gmail.com or reach out to dietterc#8665 on discord.
#
from ast import Subscript
import os
import discord
import pymongo
import utils
import time
import random
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import message
from pymongo.database import Database 
#Google api stuff
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from difflib import SequenceMatcher

#slash/buttons
from dislash import InteractionClient, ActionRow, Button, ButtonStyle, SelectMenu, SelectOption


# Check if we are running on heroku or locally 
is_heroku = os.environ.get('IS_HEROKU', None)
if is_heroku:
    TOKEN = os.environ.get('DISCORD_TOKEN', None)
    DB_PASS = os.environ.get('DB_PASS', None)
    client_secret_txt = os.environ.get('CLIENT_SECRET', None)
    #later code expects a file
    client_secret = open("client_secret.json","w")
    client_secret.write(client_secret_txt)
    client_secret.close()

else:
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    DB_PASS = os.getenv('DB_PASS')

PREFIX = '.'
CS_DISCORD_ID = 724363919035990106

random.seed()

connectedServers = []
reactionMessages = []

#Should move into server object at some point
global userHistoryList
userHistoryList = []

#channelId, roleId
global channelRoles
channelRoles = []

#userId, roleId - used for the game jam
global subscriptions
subscriptions = []

dbClient = pymongo.MongoClient("mongodb+srv://bot:" + DB_PASS + "@bot-database.p1j75.mongodb.net/bot-database?retryWrites=true&w=majority")

#read in data from db
def readInData(serverName):
    
    global dbClient
    global channelRoles

    if(serverName == "csDiscord"):
        server = utils.Server("UManitoba Computer Science Lounge")
        server.id = CS_DISCORD_ID
    elif(serverName == "game-jam"):
        #left out for now, kept here in case anyone wants to use it again
        return
        '''
        print("\nGame Jam server detected\n")
        db = dbClient["game-jam-2022"]

        collection = db["channel_roles"]
        rawValues = collection.find({},{"pair"})
        for x in rawValues:
            channelRoles.append(x["pair"])
        print("\nChannel roles imported:")
        for x in channelRoles:
            print(x)

        collection = db["subscriptions"]
        rawValues = collection.find({},{"pair"})
        for x in rawValues:
            subscriptions.append(x["pair"])
        print("\nSubscriptions imported:")
        for x in subscriptions:
            print(x)

        #Don't do the rest of this if on the game jam server
        return
        '''
    else:
        server = utils.Server(serverName)

    db = dbClient[serverName]

    #colour roles
    collection = db["colour_roles"]
    rawValues = collection.find({},{"colour"})
    for x in rawValues:
        server.colourRoles.append(x["colour"])
    print("\nColour roles imported:")
    for x in server.colourRoles:
        print(x)

    #default roles
    collection = db["default_roles"]
    rawValues = collection.find({},{"name"})
    for x in rawValues:
        server.defaultRoles.append(x["name"])
    print("\nDefault roles imported:")
    for x in server.defaultRoles:
        print(x)

    #exec roles
    collection = db["exec_roles"]
    rawValues = collection.find({},{"name"})
    for x in rawValues:
        server.execRoles.append(x["name"])
    print("\nExec roles imported:")
    for x in server.execRoles:
        print(x)

    #announcement roles
    collection = db["announcement_roles"]
    rawValues = collection.find({},{"name"})
    for x in rawValues:
        server.announcementRoles.append(x["name"])
    print("\nAnnouncement roles imported:")
    for x in server.announcementRoles:
        print(x)

    #Year roles
    collection = db["year_roles"]
    rawValues = collection.find({},{"name"})
    for x in rawValues:
        server.yearRoles.append(x["name"])
    print("\nYear roles imported:")
    for x in server.yearRoles:
        print(x)

    #Admin roles
    collection = db["admin_roles"]
    rawValues = collection.find({},{"name"})
    for x in rawValues:
        server.adminRoles.append(x["name"])
    print("\nAdmin roles imported:")
    for x in server.adminRoles:
        print(x)

    #greet message
    collection = db["greet_message"]
    rawValues = collection.find({},{"message"})
    server.greetMessage = rawValues[0]["message"]

    print("\nLoaded in the following greet message:\n" + server.greetMessage)

    #invite codes
    collection = db["invites"]
    rawValues = collection.find({})

    print("\nLoading in invites:")
    for i in rawValues:
        url = i["url"]
        uses = i["uses"]
        inviteServer = i["server"]
        roles = i["autoAssignRoles"]

        invite = utils.Invite(url,uses,inviteServer,roles)
        server.invites.append(invite)
        print(vars(invite))
    
    #user history
    collection = db["users"]
    rawValues = collection.find({})

    for i in rawValues:
        id = i["id"]
        usernames = i["usernames"]
        nicknames = i["nicknames"]

        user = utils.UserHistory(id,usernames,nicknames)
        userHistoryList.append(user)

    #last greet message
    collection = db["lastGreetMsg"]
    rawValues = collection.find({},{"messageId"})
    server.lastGreetingId = rawValues[0]["messageId"]
    print("Loaded in last greet message id: " + str(server.lastGreetingId))

    #reaction Messages
    collection = db["reaction_role_messages"]
    rawValues = collection.find({})
    for i in rawValues:
        emoji = i["emoji"]
        role = i["role"]
        messageId = i["messageId"]

        reactionMessage = utils.ReactionMessage(emoji,role,messageId)
        global reactionMessages
        reactionMessages.append(reactionMessage)
    

    print("\nFinished loading in data for " + server.displayName)

    connectedServers.append(server)

    return server


#permission check function
def hasPermission(ctx,level):
    user = ctx.message.author
    server = getServer(ctx)
    if(level == "admin"):
        for adminRole in server.adminRoles:
            admin = discord.utils.get(ctx.message.guild.roles, name=adminRole)
            if admin in user.roles:
                return True 
        return False
    elif(level == "registered"):
        roles = []
        #add every allowed role to 'roles'
        for role in server.defaultRoles:
            #convert the strings into actual role objects
            roles.append(discord.utils.get(ctx.message.guild.roles, name=role))
        for role in server.execRoles:
            roles.append(discord.utils.get(ctx.message.guild.roles, name=role))
        for role in server.adminRoles:
            roles.append(discord.utils.get(ctx.message.guild.roles, name=role))
        for role in roles:
            if role in user.roles:
                return True 
        return False

def getServer(ctx):
    for i in connectedServers:
        if ctx.message.guild.name == i.displayName:
            return i
    else:
        return -1

#Originally planned to run this every every day or so, didn't end up using it
def checkForum(server, forced): 
    if(server.id == CS_DISCORD_ID or forced):
        if(server.formLastChecked == 0 or time.time() - server.formLastChecked > 43200*2 or forced): 
            #first check or 12 hours have passed since last check
            server.formLastChecked = time.time()

            #open the responses spread-sheet
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
            client = gspread.authorize(creds)

            responsesSheet = client.open("UManitoba Computer Science Discord Signup (Responses)").sheet1

            names = responsesSheet.col_values(2)
            lastIndex = len(responsesSheet.col_values(8))

            return len(names) - lastIndex
    return 0


#Start bot
intent = discord.Intents(messages=True, members=True, guilds=True, reactions=True, voice_states=True)
bot = commands.Bot(command_prefix=PREFIX, intents = intent)
inter_client = InteractionClient(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    #guild = discord.utils.get(bot.guilds, name=GUILD)
    #channel = discord.utils.get(guild.channels, name="general")
    
    for guild in bot.guilds:
        if(guild.id == CS_DISCORD_ID):
            server = readInData("csDiscord")
        if(guild.name == "CSSA Game Jam 2022"):
            readInData("game-jam")


@bot.event
async def on_member_join(member):

    if(not member.guild.id == CS_DISCORD_ID):
        return

    global dbClient

    guild = member.guild
    guildInvites = await guild.invites()

    #guild must have a channel named "introductions"
    channel = discord.utils.get(guild.channels, name="introductions")

    server = utils.Server
    for i in connectedServers:
        if i.displayName == guild.name:
            server = i

    #db
    db = dbClient["csDiscord"]

    usedInvite = utils.Invite
    inviteFound = False
    for i in guildInvites:
        for j in server.invites:
            if i.url == j.url:
                if i.uses > j.uses:
                    await i.delete()
                    usedInvite = j
                    inviteFound = True
                    break

    if(inviteFound):
        print("Assigning roles for " + member.name)
        for role in usedInvite.autoAssignRoles:
            roleName = 0

            if(role == "CSSA Events"):
                roleName = "cssa"
            elif(role == "WICS Events"):
                roleName = "wics"
            elif(role == ".devclub Events"):
                roleName = "devclub"
            elif(role == "Movie nights"):
                roleName = "movie-night"
            elif(role == "Game nights"):
                roleName = "game-night"
            elif(role == "Student"):
                roleName = role
            elif(role == "Alumni"):
                roleName = role
            elif(role == "First Year Classes"):
                roleName = "First Year"
            elif(role == "Second Year Classes"):
                roleName = "Second Year"
            elif(role == "Third Year Classes"):
                roleName = "Third Year"
            elif(role == "Fourth Year Classes"):
                roleName = "Fourth Year"
            elif(role == "Co-op"):
                roleName = "coop"

            if(roleName != 0):
                autoRole = discord.utils.get(guild.roles, name=roleName)
                print(autoRole.name + " assigned")
                await member.add_roles(autoRole)
            else:
                print("ERROR: " + role + " not found in server")
        
        #add the announcement role no matter what (if an invite was used)
    
        autoRole = discord.utils.get(guild.roles, name="announcements")
        print(autoRole.name + " assigned")
        await member.add_roles(autoRole)

        #remove the old invite from the database/server memory
        
        if(server.id == CS_DISCORD_ID):
            db = dbClient["csDiscord"]
        else:
            db = dbClient[server.displayName]
        collection = db["invites"]
        dict = vars(usedInvite)
        collection.delete_one(dict)

        server.invites.remove(usedInvite)

        await channel.send("Welcome " + member.mention + "!")

        #delete last greet message 
        class GreetMsg:
            def __init__(self,id):
                self.messageId = id
        
        greetingFound = False

        newGreeting = discord.message
        if(server.lastGreetingId != -1):
            messages = await channel.history(limit=20).flatten()
            for message in messages:
                if(message.id == server.lastGreetingId):
                    await message.delete()
                    newGreeting = await channel.send(server.greetMessage.replace("<nl>","\n"))

                    collection = db["lastGreetMsg"]
                    dict = vars(GreetMsg(server.lastGreetingId))
                    collection.delete_one(dict)

                    server.lastGreetingId = newGreeting.id
                    greetingFound = True
        
        if(not greetingFound):
            newGreeting = await channel.send(server.greetMessage.replace("<nl>","\n"))

            collection = db["lastGreetMsg"]
            dict = vars(GreetMsg(server.lastGreetingId))
            collection.delete_one(dict)

            server.lastGreetingId = newGreeting.id

        collection = db["lastGreetMsg"]
        dict = vars(GreetMsg(newGreeting.id))
        collection.insert_one(dict)


    else:
        print("Invalid invite used for user" + member.mention + " adding unregistered role.")
        #unRegistered = discord.utils.get(guild.roles, name="unregistered")
        #print(unRegistered.name + " assigned to " + member.mention)
        #await member.add_roles(unRegistered)


    global userHistoryList

    newUser = utils.UserHistory(member.id,member.name,member.nick)
    userHistoryList.append(newUser)
    
    collection = db["users"]

    dict = vars(newUser)
    collection.insert_one(dict)



#the following two events are very similar, the only difference being a username change or a nickname change
@bot.event
async def on_member_update(before, after):

    if(not before.guild.id == CS_DISCORD_ID):
        return

    global userHistoryList

    server = utils.Server
    for i in connectedServers:
        if i.displayName == before.guild.name:
            server  = i

    #if a nickname was changed
    if(before.nick != after.nick):

        #change it locally
        for user in userHistoryList:
            if user.id == before.id:
                user.nicknames.append(after.nick)

                #change it in the db
                global dbClient
                if(server.id == CS_DISCORD_ID):
                    db = dbClient["csDiscord"]
                else:
                    db = dbClient[server.displayName]

                collection = db["users"]
                query = { "id": before.id }
                collection.delete_one(query)

                collection.insert_one(vars(user))
                print("Updating nickname for user " + before.mention + " to " + after.nick)
                return


@bot.event
async def on_user_update(before, after):

    #if(not before.guild.id == CS_DISCORD_ID):
        #return

    global userHistoryList

    #if a username was changed
    if(before.name != after.name):

        #change it locally
        for user in userHistoryList:
            if user.id == before.id:
                user.usernames.append(after.name)

                #change it in the db
                global dbClient
                db = dbClient["csDiscord"]

                collection = db["users"]
                query = { "id": before.id }
                collection.delete_one(query)

                collection.insert_one(vars(user))

                print("Updating username for user " + before.name + " to " + after.name)
                return


@bot.event
async def on_reaction_add(reaction, user):

    if(not reaction.message.guild.id == CS_DISCORD_ID):
        return

    #print(user.display_name + " sent a reaction")
    global reactionMessages

    for message in reactionMessages:
        if  not user.bot and message.messageId == reaction.message.id:
            if str(reaction.emoji) == str(message.emoji):
                role = discord.utils.get(reaction.message.guild.roles, name=message.role)
                member = discord.utils.get(reaction.message.guild.members, id=user.id)
                print("Adding role " + message.role + "to user " + user.mention)
                await member.add_roles(role)

@bot.event
async def on_reaction_remove(reaction, user):

    if(not reaction.message.guild.id == CS_DISCORD_ID):
        return

    #print(user.display_name + " sent a reaction")
    global reactionMessages

    for message in reactionMessages:
        if  not user.bot and message.messageId == reaction.message.id:
            if str(reaction.emoji) == str(message.emoji):
                role = discord.utils.get(reaction.message.guild.roles, name=message.role)
                member = discord.utils.get(reaction.message.guild.members, id=user.id)
                print("Removing role " + message.role + "to user " + user.mention)
                await member.remove_roles(role)

@bot.event
async def on_message_delete(message):

    if(not message.guild.id == CS_DISCORD_ID):
        return

    global reactionMessages
    global dbClient
    db = dbClient["csDiscord"]

    for msg in reactionMessages:
        if msg.messageId == message.id:
            reactionMessages.remove(msg)

            #remove it from the db
            collection = db["reaction_role_messages"]
            dict = { "emoji": msg.emoji, "role": msg.role, "messageId": msg.messageId }
            collection.delete_one(dict)
                    
            print("Reaction role message deleted.")

@bot.event
async def on_dropdown(inter):

    if(not inter.guild.id == CS_DISCORD_ID):
        return

    member = discord.utils.get(inter.guild.members, id=inter.author.id)

    if(inter.select_menu.custom_id == "notifications"):
        rolesToAdd = []
        rolesToRemove = []
        removeAllRoles = False

        labels = [option.label for option in inter.select_menu.selected_options]
        await inter.reply(f"Setting the following notification roles: {', '.join(labels)}", ephemeral=True)

        for option in inter.select_menu.options:
            role = discord.utils.get(inter.guild.roles, name=option.value)

            if(option in inter.select_menu.selected_options):

                if(option.value == "remove-notifications"):
                    removeAllRoles = True
                else:
                    rolesToAdd.append(role)
                
            elif(role in member.roles):
                #if it was not selected and they have it, remove it.
                rolesToRemove.append(role)
              
        if(removeAllRoles):
            roles = []
            roles.append(discord.utils.get(inter.guild.roles, name="announcements"))
            roles.append(discord.utils.get(inter.guild.roles, name="cssa"))
            roles.append(discord.utils.get(inter.guild.roles, name="wics"))
            roles.append(discord.utils.get(inter.guild.roles, name="devclub"))
            roles.append(discord.utils.get(inter.guild.roles, name="movie-night"))
            roles.append(discord.utils.get(inter.guild.roles, name="game-night"))
            roles.append(discord.utils.get(inter.guild.roles, name="server-updates"))

            for role in roles:
                await member.remove_roles(role)
        else:
            for role in rolesToAdd:
                await member.add_roles(role)
            for role in rolesToRemove:
                await member.remove_roles(role)


    elif(inter.select_menu.custom_id == "channels"):
        rolesToAdd = []
        rolesToRemove = []
        removeAllRoles = False

        labels = [option.label for option in inter.select_menu.selected_options]
        await inter.reply(f"Setting the following channel access roles: {', '.join(labels)}", ephemeral=True)

        for option in inter.select_menu.options:
            role = discord.utils.get(inter.guild.roles, name=option.value)

            if(option in inter.select_menu.selected_options):

                if(option.value == "remove-roles"):
                    removeAllRoles = True
                else:
                    rolesToAdd.append(role)
                
            elif(role in member.roles):
                #if it was not selected and they have it, remove it.
                rolesToRemove.append(role)
     
        if(removeAllRoles):
            roles = []
            roles.append(discord.utils.get(inter.guild.roles, name="First Year"))
            roles.append(discord.utils.get(inter.guild.roles, name="Second Year"))
            roles.append(discord.utils.get(inter.guild.roles, name="Third Year"))
            roles.append(discord.utils.get(inter.guild.roles, name="Fourth Year"))
            roles.append(discord.utils.get(inter.guild.roles, name="Tenth Year"))
            roles.append(discord.utils.get(inter.guild.roles, name="coop"))
            
            for role in roles:
                await member.remove_roles(role)
        else:
            for role in rolesToAdd:
                await member.add_roles(role)
            for role in rolesToRemove:
                await member.remove_roles(role)


    elif(inter.select_menu.custom_id == "colour"):
        rolesToAdd = []
        rolesToRemove = []
        removeAllRoles = False

        labels = [option.label for option in inter.select_menu.selected_options]
        await inter.reply(f"Setting your colour to: {', '.join(labels)}\n*note: it may take a moment to apply.*", ephemeral=True)

        server = utils.Server
        for i in connectedServers:
            if i.id == CS_DISCORD_ID:
                server  = i

        #remove all colours first
        roles = []
        for x in server.colourRoles:
            roles.append(discord.utils.get(inter.guild.roles, name=x))
            
        for i in roles:
            await member.remove_roles(i)
        
        for option in inter.select_menu.options:
            role = discord.utils.get(inter.guild.roles, name=option.value)
            
            if(option in inter.select_menu.selected_options):

                if(option.value == "remove-roles"):
                    removeAllRoles = True
                else:
                    rolesToAdd.append(role)
     
        if(not removeAllRoles):
            for role in rolesToAdd:
                if role != None:
                    await member.add_roles(role)

    elif(inter.select_menu.custom_id == "status"):

        labels = [option.label for option in inter.select_menu.selected_options]
        await inter.reply(f"Setting your status to: {''.join(labels)}", ephemeral=True)

        server = utils.Server
        for i in connectedServers:
            if i.id == CS_DISCORD_ID:
                server  = i

        #remove old role
        await member.remove_roles(discord.utils.get(inter.guild.roles, name="Student"))
        await member.remove_roles(discord.utils.get(inter.guild.roles, name="Alumni"))

        for option in inter.select_menu.options:
            role = discord.utils.get(inter.guild.roles, name=option.value)
            
            if(option in inter.select_menu.selected_options):
                await member.add_roles(role)
     

#On every message
@bot.event
async def on_message(message):
    john = discord.utils.get(message.guild.emojis, name="cooljohn")
    kirby = discord.utils.get(message.guild.emojis, name="cursed_kirby")

    words = message.content.split(" ")
    for w in words:
        if w.lower() == "processing":
            if random.randint(0,1) == 0:
                await message.add_reaction(john)
                break
        if w.lower() == "cursed" or w.lower() == "kirby":
            if random.randint(0,1) == 0:
                await message.add_reaction(kirby)
                break

    #THIS MUST BE HERE. If it isn't, commands will not work.
    await bot.process_commands(message)



##------------ GAME JAM UPDATE ------------##

@bot.event
async def on_voice_state_update(member,before,after):

    global channelRoles
    global subscriptions

    if(not member.guild.name == "CSSA Game Jam 2022"):
        return

    localSubs = []
    for pair in subscriptions:
        if(pair[0] == member.id):
            localSubs.append(pair[1])

    if(before.channel != None):
        #remove old role
        channelId = before.channel.id

        for pair in channelRoles:
            if(pair[0] == channelId):
                role = discord.utils.get(member.guild.roles, id=int(pair[1]))

                if(not pair[1] in localSubs):
                    await member.remove_roles(role)
                    print("Removed role " + role.name + " from user " + member.name)
                else:
                    print("Role " + role.name + " not changed for user " + member.name)

    if(after.channel != None):
        #add old role
        channelId = after.channel.id

        for pair in channelRoles:
            if(pair[0] == channelId):
                role = discord.utils.get(member.guild.roles, id=int(pair[1]))

                if(not pair[1] in localSubs):
                    await member.add_roles(role)
                    print("Added role " + role.name + " to user " + member.name)
                else:
                    print("Role " + role.name + " not changed for user " + member.name)
    
@bot.command()
@commands.has_role('bot-control')
async def creategroup(ctx, *args):
    global dbClient
    global channelRoles

    if(not ctx.message.guild.name == "CSSA Game Jam 2022"):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(len(args) == 2):

        roleId = discord.utils.get(ctx.message.guild.roles, name=args[0]).id
        channelId = discord.utils.get(ctx.message.guild.channels, name=args[1]).id

        db = dbClient["game-jam-2022"]

        collection = db["channel_roles"]
        dict = { "pair": (channelId,roleId) }
        collection.insert_one(dict)
        channelRoles.append([channelId,roleId])
        await ctx.send("Group created for " + args[0])


@bot.command()
@commands.has_role('bot-control')
async def removegroup(ctx, *args):
    global dbClient
    global channelRoles

    if(not ctx.message.guild.name == "CSSA Game Jam 2022"):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(len(args) == 1):
        roleId = discord.utils.get(ctx.message.guild.roles, name=args[0]).id
        channelId = ''
        for pair in channelRoles:
            if(pair[1] == roleId):
                channelId = pair[0]
                channelRoles.remove([channelId,roleId])
                break
    
        db = dbClient["game-jam-2022"]

        collection = db["channel_roles"]
        dict = { "pair": (channelId,roleId) }
        collection.delete_one(dict)
        await ctx.send("Group deleted for " + args[0])


@bot.command()
async def join(ctx, *args):

    global dbClient
    global channelRoles
    global subscriptions

    if(not ctx.message.guild.name == "CSSA Game Jam 2022"):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(ctx.message.author.voice == None and len(args) == 0):
        await ctx.send("Error: You must be in a groups voice channel.")
        return

    roleId = -1

    if(len(args) == 0):
        channelId = ctx.message.author.voice.channel.id
        #get role associated with this channel
        for pair in channelRoles:
            if(pair[0] == channelId):
                roleId = pair[1]
                break

        if(roleId == -1 or channelId == None):
            await ctx.send("Error: You must be in a groups voice channel.")
            return
        
        role = discord.utils.get(ctx.message.author.guild.roles, id=roleId)

    elif(len(args) == 1):
        role = discord.utils.get(ctx.message.author.guild.roles, name=args[0])

        if(role == None):
            await ctx.send("Error: No role found for `" + args[0] + "`")
            return

        await ctx.message.author.add_roles(role)

    else:
        await ctx.send("Error: Please use 0-1 arguments.")
        return

    db = dbClient["game-jam-2022"]

    collection = db["subscriptions"]
    dict = { "pair": (ctx.message.author.id,role.id) }
    collection.insert_one(dict)
    subscriptions.append([ctx.message.author.id,role.id])
    await ctx.send("You have joined group " + role.name)


@bot.command()
async def leave(ctx, *args):

    global dbClient
    global channelRoles
    global subscriptions

    if(not ctx.message.guild.name == "CSSA Game Jam 2022"):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(ctx.message.author.voice == None and len(args) == 0):
        await ctx.send("Error: You must be in a groups voice channel.")
        return

    roleId = -1

    if(len(args) == 0):
        channelId = ctx.message.author.voice.channel.id
        #get role associated with this channel
        for pair in channelRoles:
            if(pair[0] == channelId):
                roleId = pair[1]
                break

        if(roleId == -1 or channelId == None):
            await ctx.send("Error: You must be in a groups voice channel.")
            return
        
        role = discord.utils.get(ctx.message.author.guild.roles, id=roleId)

    elif(len(args) == 1):
        role = discord.utils.get(ctx.message.author.guild.roles, name=args[0])

        if(role == None):
            await ctx.send("Error: No role found for `" + args[0] + "`")
            return

        if(ctx.message.author.voice == None):
            await ctx.message.author.remove_roles(role)

    else:
        await ctx.send("Error: Please use 0-1 arguments.")
        return

    db = dbClient["game-jam-2022"]

    collection = db["subscriptions"]
    dict = { "pair": (ctx.message.author.id,role.id) }
    collection.delete_one(dict)
    subscriptions.remove([ctx.message.author.id,role.id])
    await ctx.send("You have left group " + role.name)


#### Commands ####

#default format for commands, where the function name is the command to type
#the has_role part here is the 'easy' way to lock out commands, I like to do it the manual way (checking myself)
@bot.command()
@commands.has_role('admin')
async def test(ctx, *, args=None):
    #send the arguments of the command back to the user
    await ctx.send(''.join(args))

#get this servers ID
@bot.command()
@commands.has_role('admin')
async def id(ctx, *, args=None):
    await ctx.send(ctx.message.guild.id)


#forcibly check for forum responses
@bot.command()
async def forcecheck(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(not hasPermission(ctx,"admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    responses = checkForum(getServer(ctx),True)
    if(responses <= 0):
        await ctx.send("There are no new form responses.")
    else:
        await ctx.send("There are `" + str(responses) + "` new form responses.")



@bot.command()
async def iam(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)

    if hasPermission(ctx,"registered"):
        if(len(args) != 0):

            user = ctx.message.author
            #check if the user is adding a year role 
            year = args[0].lower().capitalize() + " Year"

            if(args[0] in server.colourRoles):

                #check if the user has a colour role already
                role = discord.Role
                roleFound = False
                for i in server.colourRoles:
                    if discord.utils.get(ctx.message.guild.roles, name=i) in user.roles:
                        role = discord.utils.get(ctx.message.guild.roles, name=i)
                        roleFound = True
                        break

                if(roleFound):
                    await user.remove_roles(role)
                    
                newRole = discord.utils.get(ctx.message.guild.roles, name=args[0])
                if(newRole):
                    await user.add_roles(newRole)
                    await ctx.send("Colour role `" + newRole.name + "` set.")
                else:
                    await ctx.send("Error: Role `" + args[0] + "` not found in discord. This may be a backend issue.")

            elif(year in server.yearRoles):
                if(len(args) == 2 and args[1] == 'year'):
                    if(discord.utils.get(ctx.message.guild.roles, name=year) in user.roles):
                        await ctx.send("Error: You already have the `" + year + "` role.")
                    else:
                        await user.add_roles(discord.utils.get(ctx.message.guild.roles, name=year))
                        sentmsg = await ctx.send("`" + year + "` role added.")
                        
                        if year.lower() == "tenth year":
                            await sentmsg.delete(delay=3)
                            await ctx.message.delete(delay=3)

                else:
                    await ctx.send("Error: Correct format is `" + PREFIX + "iam " + args[0] + " year`.")

            elif(args[0].lower() == "coop" or args[0].lower() == "co-op"):
                if(discord.utils.get(ctx.message.guild.roles, name="coop") in user.roles):
                        await ctx.send("Error: You already have the `coop` role.")
                else:
                    await user.add_roles(discord.utils.get(ctx.message.guild.roles, name="coop"))
                    await ctx.send("`coop` role added.")

            else:
                await ctx.send("Error: Year or colour role `" + args[0] + "` not found.")
        else:
            await ctx.send("Error: Year or colour role must be specified")
    else:
        await ctx.send("Error: You do not have permission to use this command.")

@bot.command()
async def iamnot(ctx, *args):
    await iamn(ctx, *args)

@bot.command()
async def iamn(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)

    if hasPermission(ctx,"registered"):
        if(len(args) != 0):

            user = ctx.message.author
            year = args[0].lower().capitalize() + " Year"

            if(args[0] in server.colourRoles):
                #check if the user has a colour role to remove
                role = discord.Role
                roleFound = False
                for i in server.colourRoles:
                    if discord.utils.get(ctx.message.guild.roles, name=i) in user.roles:
                        role = discord.utils.get(ctx.message.guild.roles, name=i)
                        roleFound = True
                        break
                #remove colour role, check which one they have then remove it 
                if(roleFound):
                    if (role.name == args[0]):
                        await user.remove_roles(role)
                        await ctx.send("Colour role `" + role.name + "` removed.")
                    else:
                        await ctx.send("Error: You do not have the role `" + args[0] + "`.")
                else:
                    await ctx.send("Error: No colour role to remove.")

            elif(year in server.yearRoles):
                if(len(args) == 2 and args[1] == 'year'):
                    role = discord.utils.get(ctx.message.guild.roles, name=year)
                    if role in user.roles:
                        await user.remove_roles(role)
                        sentmsg = await ctx.send("Year role `" + role.name + "` removed.")
                        
                        if year.lower() == "tenth year":
                            await sentmsg.delete(delay=3)
                            await ctx.message.delete(delay=3)

                    else:
                        await ctx.send("Error: You do not have the role `" + role.name + "`.")
                else:
                    await ctx.send("Error: Correct format is `" + PREFIX + "iamn " + args[0] + " year`.")

            elif(args[0].lower() == "coop" or args[0].lower() == "co-op"):
                if(not discord.utils.get(ctx.message.guild.roles, name="coop") in user.roles):
                        await ctx.send("Error: You do not have the `coop` role.")
                else:
                    await user.remove_roles(discord.utils.get(ctx.message.guild.roles, name="coop"))
                    await ctx.send("`coop` role removed.")

            else:
                await ctx.send("Error: Year or colour role `" + args[0] + "` not found.")
        else:
            await ctx.send("Error: Year or colour role must be specified")
    else:
        await ctx.send("Error: You do not have permission to use this command.")

@bot.command()
async def colour(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)
    global dbClient
    if(server.id == CS_DISCORD_ID):
        db = dbClient["csDiscord"]
    else:
        db = dbClient[server.displayName]
    
    if(not hasPermission(ctx,"admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(len(args) == 0):
        await ctx.send("Error: Correct format is: `" + PREFIX + r"colour add/remove {colour}`.")
        return

    if(args[0] == 'add'):
        # adding colours
        if(len(args) == 3):
            colour = args[1]
            if(args[2].lower() not in server.colourRoles and args[2].lower() not in server.lowerRoleList()):
                if(colour[0] == '#' and len(colour) == 7):
                    try:
                        guild = ctx.guild
                        roleName = args[2].lower()
                        await guild.create_role(name=roleName,colour=discord.Colour(int(colour[1:], 16)))
                        await ctx.send("Colour role: `" + roleName + "` added.")

                        #add the new colour to the db, then add it to our list
                        collection = db["colour_roles"]
                        dict = { "colour": roleName }
                        collection.insert_one(dict)

                        server.colourRoles.append(roleName)
                    except:
                        await ctx.send("Error: Invalid hex input: " + colour)
                else:
                    await ctx.send("Error: Invalid hex input: " + colour)
            else:
                await ctx.send("Error: Role with that name already exists.")
        else: 
            await ctx.send("Error: Correct format is: `" + PREFIX + r"colour add #{hexColour} {label}`")

    elif(args[0] == 'remove'):
        #removing colours 
        if(len(args) == 2):
            role = discord.utils.get(ctx.message.guild.roles, name=args[1].lower())
            if(args[1].lower() in server.colourRoles and role):
                try:
                    await role.delete()
                    #colour exits, remove it
                    server.colourRoles.remove(args[1].lower())
                    
                    #remove it from the db
                    collection = db["colour_roles"]
                    dict = { "colour": args[1].lower() }
                    collection.delete_one(dict)
                    
                    await ctx.send("Colour role `" + args[1].lower() + "` deleted.")

                except discord.Forbidden:
                    await bot.say("Error: Missing Permissions to delete this role.")

            else:
                await ctx.send("Error: Colour role `" + args[1] + "` not found.")
        else:
            await ctx.send("Error: Correct format is: `" + PREFIX + r"colour remove {colour}`")
    else:
        await ctx.send("Error: Correct format is: `" + PREFIX + r"colour add/remove {colour}`.")
    
@bot.command()
async def colours(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)
    message = ""

    for x in server.colourRoles:
        message += x + "\n"

    await ctx.send("Colour roles:```" + message + "\nUsage: .iam <colour>```")

@bot.command()
async def notify(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)

    if(not hasPermission(ctx,"registered")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(len(args) == 0 or len(args) > 1):
        await ctx.send("Error: Correct format is: `" + PREFIX + r"notify {category}`.")
        return

    if(args[0].lower() in server.announcementRoles):
        role = discord.utils.get(ctx.message.guild.roles, name=args[0].lower())
        user = ctx.message.author
        if(role):
            if role not in user.roles:
                await user.add_roles(role)
                await ctx.send("Announcement role `" + role.name + "` set.")
            else:
                await ctx.send("Error: You already have this role.")
        else:
            await ctx.send("Error: Role `" + args[0] + "` not found in discord. This may be a backend issue.")
    elif(args[0].lower() == 'all'):
        user = ctx.message.author
        rolesAdded = []
        for i in server.announcementRoles:
            role = discord.utils.get(ctx.message.guild.roles, name=i)
            if(role not in user.roles):
                await user.add_roles(role)
                rolesAdded.append(i)
        if(len(rolesAdded) == 0):
            await ctx.send("Error: You already have all available announcement roles.")
        else:
            if(len(rolesAdded) > 1):
                rolesString = ", ".join(rolesAdded)
                await ctx.send("Announcement roles `" + rolesString + "` set.")
            else:
                await ctx.send("Announcement role `" + rolesAdded[0] + "` set.")
    else:
        await ctx.send("Error: Role `" + args[0] + "` not found.")


@bot.command()
async def unnotify(ctx, *args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)

    if(not hasPermission(ctx,"registered")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(len(args) == 0 or len(args) > 1):
        await ctx.send("Error: Correct format is: `" + PREFIX + r"unnotify {category}`.")
        return

    if(args[0].lower() in server.announcementRoles):
        role = discord.utils.get(ctx.message.guild.roles, name=args[0].lower())
        user = ctx.message.author
        if(role):
            if role in user.roles:
                await user.remove_roles(role)
                await ctx.send("Announcement role `" + role.name + "` removed.")
            else:
                await ctx.send("Error: You do not have this role.")
        else:
            await ctx.send("Error: Role `" + args[0] + "` not found in discord. This may be a backend issue.")
    elif(args[0].lower() == 'all'):
        user = ctx.message.author
        rolesRemoved = []
        for i in server.announcementRoles:
            role = discord.utils.get(ctx.message.guild.roles, name=i)
            if(role in user.roles):
                await user.remove_roles(role)
                rolesRemoved.append(i)
        if(len(rolesRemoved) == 0):
            await ctx.send("Error: You do not have any announcement roles to remove.")
        else:
            if(len(rolesRemoved) > 1):
                rolesString = ", ".join(rolesRemoved)
                await ctx.send("Announcement roles `" + rolesString + "` removed.")
            else:
                await ctx.send("Announcement role `" + rolesRemoved[0] + "` removed.")
    else:
        await ctx.send("Error: Role `" + args[0] + "` not found.")


@bot.command()
async def setgreetmessage(ctx, *, arg): 

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)
    global dbClient
    db = dbClient[server.displayName]

    if(not hasPermission(ctx, "admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(arg):
        await ctx.send("New greet message set to:\n```" + arg + "```")

        collection = db["greet_message"]
        dict = { "message": server.greetMessage }
        new_dict = { "$set": { "message": arg } }
        collection.update_one(dict, new_dict)
        greetMessage = arg

@setgreetmessage.error
async def setgreetmessage_error(ctx, error):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)
    global dbClient
    db = dbClient[server.displayName]

    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        if(not hasPermission(ctx, "admin")):
            await ctx.send("Error: You do not have permission to use this command.")
            return
        await ctx.send("Greet message removed.")
        collection = db["greet_message"]
        dict = { "message": server.greetMessage }
        new_dict = { "$set": { "message": "" } }
        collection.update_one(dict, new_dict)
        server.greetMessage = ""
       
#not sure if this is still used tbh
@bot.command()
async def autoassignrole(ctx,*args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)

    if(not hasPermission(ctx, "admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(len(args) != 0):
        await ctx.send("Error: No parameters are accepted for this command.")
        return

    server.autoAssign = not server.autoAssign

    if(server.autoAssign):
        await ctx.send("Auto assignment of roles enabled.")
    elif(not server.autoAssign):
        await ctx.send("Auto assignment of roles disabled.")


bot.remove_command("help") 
@bot.command()
async def help(ctx,*args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(len(args) != 0):
        if(args[0] == "admin"):
            if(hasPermission(ctx, "admin")):
                file = open("templates/admin_help_command1.txt","r")
                content1 = file.read()
                file.close()

                file = open("templates/admin_help_command2.txt","r")
                content2 = file.read()
                file.close()

                embed = discord.Embed(color=0x8e1600)
                embed.add_field(name="Admin commands:", value=content1, inline=False)
                embed.add_field(name="Part 2:", value=content2, inline=False)

                channel = discord.utils.get(ctx.guild.channels, name="admin-bot-commands")
                await channel.send(embed=embed)
                

                await ctx.send("Output sent to *[REDACTED]*")
            else:
                await ctx.send("Error: You do not have permission to use this command.")
        else:
            await ctx.send("Error: Command must be `.help` or `.help admin`")
    else:
        file = open("templates/help_command.txt","r")
        content = file.read()
        file.close()

        embed = discord.Embed(color=0x00c3e6)
        embed.add_field(name="Available commands", value=content, inline=False)
        await ctx.send(embed=embed)


@bot.command()
async def form(ctx,*args):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    await ctx.send("https://forms.gle/C11YVJDVW2DhcbjXA")


@bot.command()
async def history(ctx, *, args=None):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(not hasPermission(ctx, "admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return
    
    server = getServer(ctx)
    global dbClient
    global userHistoryList
    

    if(args != None):

        #check the whole list for a match
        searchString = ''.join(args).lower()
        closest = [None,0]

        for user in userHistoryList:
            
            if(user.id == searchString):
                await ctx.send("Exact match found for `" + searchString + "`:")
                await ctx.send(user)
                return

            for username in user.usernames:
                if(username.lower() == searchString):
                    await ctx.send("Match found for `" + searchString + "`:")
                    await ctx.send(user)
                    return
                else:
                    #see how close to a match we are
                    similarityRatio = SequenceMatcher(None, username.lower(), searchString).ratio()
                    if similarityRatio > closest[1]:
                        closest[0] = user
                        closest[1] = similarityRatio

            for nickname in user.nicknames:
                if nickname != None:
                    if(nickname.lower() == searchString):
                        await ctx.send("Match found for `" + searchString + "`:")
                        await ctx.send(user)
                        return
                    else:
                        #see how close to a match we are
                        similarityRatio = SequenceMatcher(None, username.lower(), searchString).ratio()
                        if similarityRatio > closest[1]:
                            closest[0] = user
                            closest[1] = similarityRatio

        await ctx.send("No match found for `" + searchString + "`")

        if(closest[0] != None):
            await ctx.send("Closest result: (" + str(closest[1]) + r"% similarity)")
            await ctx.send(closest[0])

    else:
        await ctx.send("Error: Please enter at least one argument")


#send a message and give it a role assigning reaction
@bot.command()
async def reactionRole(ctx, *, args=None): 

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)
    global dbClient
    db = dbClient["csDiscord"]

    if(not hasPermission(ctx, "admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(args != None):
        guild = discord.utils.get(bot.guilds, name=server.displayName)

        #assume message is in the format CHANNEL,EMOJI,ROLE##MESSAGE
        rawMessage = args.split("##")
        splitArgs = rawMessage[0].split(",")
        channel = discord.utils.get(guild.channels, name=splitArgs[0])
        emoji = splitArgs[1]
        role = discord.utils.get(guild.roles, name=splitArgs[2])
        message = rawMessage[1]

        if(channel):
            sentMessage = await channel.send(message)
            await sentMessage.add_reaction(emoji)

            collection = db["reaction_role_messages"]
            dict = { "emoji": splitArgs[1], "role": role.name, "messageId": sentMessage.id }
            collection.insert_one(dict)
            global reactionMessages
            reactionMessages.append(utils.ReactionMessage(emoji,role.name,sentMessage.id))
        
@bot.command()
async def setupRolesChannel(ctx, *, args=None): 

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)
    user = ctx.message.author

    global dbClient
    db = dbClient["csDiscord"]

    #only _ for now - ADD YOUR ID HERE
    if(not user.id == 0):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    text_channel = discord.utils.get(ctx.guild.channels, name=args)

    #Channel access roles 
    yearMsg = await text_channel.send(
        "\n__**Channel Access roles:**__ \nWant access to text channels related to the COMP classes you are in?\nSelect any of the following!",
        components=[
            SelectMenu(
                custom_id="channels",
                placeholder="Choose as many options as you like",
                max_values=5,
                min_values=0,
                options=[
                    SelectOption("First year", "First Year", "Gain access to COMP 1xxx channels","1️⃣"),
                    SelectOption("Second year", "Second Year", "Gain access to COMP 2xxx channels","2️⃣"),
                    SelectOption("Third year", "Third Year", "Gain access to COMP 3xxx channels","3️⃣"),
                    SelectOption("Fourth year", "Fourth Year", "Gain access to COMP 4xxx channels","4️⃣"),
                    SelectOption("Co-op", "coop", "Gain access to channels related to the CS co-op program","🖥️"),
                    SelectOption("Remove all years", "remove-roles", "Remove all year roles. Overwrites all other options.", "❌")
                ]
            )
        ]
    )
    yearMsg2 = await text_channel.send("You can also use the command `.iam <first/second/etc..> year` to manually add the roles. To remove a year role use `.iamn <year>`, `.iamnot <year>`, or de-select it in the menu above.\n*Note: Course specific channels only exist for courses that are being taught in the current term.*")


    #Notification roles
    notificationMsg = await text_channel.send(
        "**~**\n\n__**Notification roles:**__ \nSelect what you would like to receive notifications about on the server!",
        components=[
            SelectMenu(
                custom_id="notifications",
                placeholder="Choose as many options as you like",
                max_values=7,
                min_values=0,
                options=[
                    SelectOption("Announcements", "announcements", "Server-wide announcements"),
                    SelectOption("CSSA", "cssa", "Announcements from the CSSA"),
                    SelectOption("WICS", "wics", "Announcements from WICS"),
                    SelectOption(".devclub", "devclub", "Announcements from .devclub"),
                    SelectOption("Movie nights", "movie-night", "Movie nights taking place on this server"),
                    SelectOption("Game nights", "game-night", "Game nights taking place on this server"),
                    SelectOption("Server updates", "server-updates", "General announcements regarding the server (updates, maintenance, etc.)"),
                    SelectOption("Remove all notification roles", "remove-notifications", "Overwrites all other options.")
                ]
            )
        ]
    )
    notificationMsg2 = await text_channel.send("You can also use the command `.notify <role>` to manually add the roles. To remove a year role use `.unnotify <role>`, or de-select it in the menu above.\n*By default, all users will have the announcements role. Use `.unnotify announcements` or the \"Remove all notification roles\" option above to opt out.*")


    #Colour role
    colourMsg = await text_channel.send(
        "**~**\n\n__**Colour roles:**__ \nWant to change the colour of your name on the server?\nSelect one of the following!",
        components=[
            SelectMenu(
                custom_id="colour",
                placeholder="Choose 1 option",
                max_values=1,
                options=[
                    SelectOption("Purple", "purple", "Set the colour of your name to purple!", "🍇"),
                    SelectOption("Red", "red", "Set the colour of your name to red!","❤️"),
                    SelectOption("Yellow", "yellow", "Set the colour of your name to yellow!","🍋"),
                    SelectOption("Aqua", "aqua", "Set the colour of your name to aqua!","💎"),
                    SelectOption("Pink", "pink", "Set the colour of your name to pink!","🍑"),
                    SelectOption("Orange", "orange", "Set the colour of your name to orange!","🟠"),
                    SelectOption("Lime", "lime", "Set the colour of your name to lime!","🟢"),
                    SelectOption("Green", "green", "Set the colour of your name to green!","🐍"),
                    SelectOption("Blue", "blue", "Set the colour of your name to blue!","🆒"),
                    SelectOption("Gold", "gold", "Set the colour of your name to gold!","💰"),
                    SelectOption("Black", "black", "Set the colour of your name to black!","🖤"),
                    SelectOption("No colour", "remove-colour", "Remove any colour from your name.","❌")
                ]
            )
        ]
    )
    colourMsg2 = await text_channel.send("You can also use the command `.iam <colour>` to set your colour.\nUse `.iamnot <colour>`, `.iamn <colour>` or select the \"No colour\" option in the menu above to remove your colour. If you want to suggest a colour, share it in #suggestions-and-feedback!\nTo see the full list of colours, use the command `.colours`")

    #Colour role
    statusMsg = await text_channel.send(
        "**~**\n\n__**Student status:**__ \nAre you a student or alumni? Select one of the following:",
        components=[
            SelectMenu(
                custom_id="status",
                placeholder="Choose 1 option",
                max_values=1,
                options=[
                    SelectOption("Student", "Student", "Set your status to Student", "📖"),
                    SelectOption("Alumni", "Alumni", "Set your status to Alumni","🎓"),
                ]
            )
        ]
    )

    await text_channel.send("**~**\n\nTo receive any of the above roles, you must have the either the student or alumni role. Unless you joined through an event invite, it should be given to you shortly after you join. Let us know if you should have it but don't!")


@bot.command()
async def genFormInvites(ctx, *, args=None):

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    if(not hasPermission(ctx, "admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    server = getServer(ctx)
    guild = discord.utils.get(bot.guilds, name=server.displayName)
    inviteChannel = discord.utils.get(guild.channels, name="introductions")
    global dbClient
    db = dbClient["csDiscord"]
    collection = db["invites"]

    responses = checkForum(server,True)
    if(responses <= 0):
        await ctx.send("There are no new form responses.")
        return

    await ctx.send(str(responses) + " new responses. Generating invites now...")
    #open the responses spread-sheet
    scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)
    responsesSheet = client.open("UManitoba Computer Science Discord Signup (Responses)").sheet1

    emails = responsesSheet.col_values(3)
    names = responsesSheet.col_values(2)
    rawChannelRoles = responsesSheet.col_values(6)
    rawNotificationRoles = responsesSheet.col_values(7)
    statusRole = responsesSheet.col_values(4)
    index = len(responsesSheet.col_values(8)) + 1 #the index of the first new response

    def checkEmail(email, currentIndex):
        email = email.replace(" ","").lower()

        if(not email.endswith("@myumanitoba.ca" or email.endswith("@learning.icmanitoba.ca"))):
            return False
        for i in range(currentIndex - 1):
            if(email == emails[i].replace(" ","").lower()):
                return False
        return True

    for i in range(index, len(emails) + 1):

        if(checkEmail(emails[i-1],i)):

            try:
                channelRoles = rawChannelRoles[i-1].split(", ")
            except:
                channelRoles = []
            
            try:
                notificationRoles = rawNotificationRoles[i-1].split(", ")
            except:
                notificationRoles = []

            roles = []
            for j in channelRoles:
                roles.append(j)
            for j in notificationRoles:
                roles.append(j)

            roles.append(statusRole[i-1])

            
            #generate an invite link
            newInvite = await inviteChannel.create_invite(max_uses=5, unique=True, reason="Created invite for user: " + responsesSheet.row_values(i)[1])
            #generate a utils link to be saved server side
            invite = utils.Invite(newInvite.url,0,server.displayName,roles)
            server.invites.append(invite)
            #add it to the database
            dict = vars(invite)
            collection.insert_one(dict)

            roleString = ""
            for x in roles:
                roleString += x + "\n"

            await ctx.send("```Name: " + names[i-1] + "\nEmail: " + emails[i-1] + "\nInvite: " + newInvite.url + "\nRoles:\n" + roleString + "```")

            responsesSheet.update_cell(i,8,newInvite.url)
        else:
            responsesSheet.update_cell(i,8,"Flagged")


##---------------Fun commands---------------
@bot.command()
async def sendmessage(ctx, *, arg): 

    if(not ctx.message.guild.id == CS_DISCORD_ID):
        await ctx.send("Error: This command is not enabled on this server.")
        return

    server = getServer(ctx)

    if(not hasPermission(ctx, "admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    guild = discord.utils.get(bot.guilds, name=server.displayName)

    #assume message is in the format CHANNEL##MESSAGE
    rawMessage = arg.split("##")
    channel = discord.utils.get(guild.channels, name=rawMessage[0])
    message = rawMessage[1]

    if(channel):
        await channel.send(message)

@sendmessage.error
async def sendmessage_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        if(not hasPermission(ctx, "admin")):
            await ctx.send("Error: You do not have permission to use this command.")
            return
        await ctx.send("Error: No message to send.")


@bot.command()
async def nothing(ctx,*args): 
    pass


##---------------Commands Enabled on other servers---------------

@bot.command()
async def cssa(ctx,*args):
    file = open("templates/cssa.txt","r")
    await ctx.send(file.read())
    file.close()


@bot.command()
async def wics(ctx,*args): 
    file = open("templates/wics.txt","r")
    await ctx.send(file.read())
    file.close()


@bot.command()
async def devclub(ctx,*args):
    file = open("templates/devclub.txt","r")
    await ctx.send(file.read())
    file.close()


#permission check for external servers
def hasExternalPermission(ctx):
    role = discord.utils.get(ctx.message.guild.roles, name="admin")

    if(role in ctx.message.author.roles):
        return True
    else:
        return False

@bot.command()
async def generateInvites(ctx,*args):
    #Generate the given number of invites for the server this command was run on.

    if(not hasExternalPermission(ctx)):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    guild = ctx.message.guild
    inviteChannel = discord.utils.get(guild.channels, name="introductions")

    if(len(args) == 1):
        inviteList = []
        for i in range(int(args[0])):
            invite = await inviteChannel.create_invite(max_uses=1, unique=True, reason="Created invite through bot.")
            inviteList.append(invite.url)

        await ctx.send("```Invites generated:\n" + "\n".join(inviteList) + "```")

    else:
        await ctx.send("Error: Exactly one argument (int) must be given.")


bot.run(TOKEN)

