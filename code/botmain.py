import os
import discord
import pymongo
import utils
import time
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import message
from pymongo.database import Database 
#Google api stuff
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Check if we are running on heroku or locally 
is_heroku = os.environ.get('IS_HEROKU', None)
if is_heroku:
    TOKEN = os.environ.get('DISCORD_TOKEN', None)
    DB_PASS = os.environ.get('DB_PASS', None)
else:
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    DB_PASS = os.getenv('DB_PASS')

PREFIX = '.'

connectedServers = []
formattedEmails = []

dbClient = pymongo.MongoClient("mongodb+srv://bot:" + DB_PASS + "@bot-database.p1j75.mongodb.net/bot-database?retryWrites=true&w=majority")

#read in data from db
def readInData(serverName):
    
    if(serverName == "csDiscord"):
        server = utils.Server("UManitoba Computer Science Lounge")
    else:
        server = utils.Server(serverName)

    global dbClient

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

    print("\nFinished loading in data for " + server.displayName)

    connectedServers.append(server)

    return server


#permission check function
def hasPermission(ctx,level):
    user = ctx.message.author
    server = getServer(ctx)
    if(level is "admin"):
        for adminRole in server.adminRoles:
            admin = discord.utils.get(ctx.message.guild.roles, name=adminRole)
            if admin in user.roles:
                return True 
        return False
    elif(level is "registered"):
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

def checkForum(server, forced):
    #check only the UofM server for now, functionality for other servers will be added later. 

    if(server.displayName == "UManitoba Computer Science Lounge" or forced):
        if(server.formLastChecked == 0 or time.time() - server.formLastChecked > 43200*2 or forced): 
            #first check or 12 hours have passed since last check
            server.formLastChecked = time.time()

            #open the responses spread-sheet
            scope = ['https://spreadsheets.google.com/feeds',
                     'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
            client = gspread.authorize(creds)

            responsesSheet = client.open("Responses to discord signup").sheet1

            names = responsesSheet.col_values(2)
            lastIndex = len(responsesSheet.col_values(8))

            return len(names) - lastIndex
    return 0

#Start bot
intent = discord.Intents(messages=True, members=True, guilds=True)
bot = commands.Bot(command_prefix=PREFIX, intents = intent)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    #guild = discord.utils.get(bot.guilds, name=GUILD)
    #channel = discord.utils.get(guild.channels, name="general")
    
    for guild in bot.guilds:
        if(guild.name == "UManitoba Computer Science Lounge"):
            server = readInData("csDiscord")
        else:
            server = readInData(guild.name.replace(" ","-"))
        #checkForum(server,False)


@bot.event
async def on_member_join(member):

    guild = member.guild

    #guild must have a channel named "introductions"
    channel = discord.utils.get(guild.channels, name="introductions")

    server = utils.Server
    for i in connectedServers:
        if i.displayName == guild.name:
            server  = i

    if(server.greetMessage != ""):
        await channel.send(server.greetMessage.replace(f"%user%", member.mention))

    usedInvite = utils.Invite

    for i in guild.invites():
        for j in server.invites:
            if i.url == j.url:
                if i.uses > j.uses:
                    await i.delete("Invite used on user " + member.mention)
                    usedInvite = j
                    break

    print("Assigning roles for " + member.name)
    for role in usedInvite.autoAssignRoles:
        autoRole = discord.utils.get(guild.roles, name=role)
        print(autoRole.name + " assigned")
        await member.add_roles(autoRole)

    #remove the old invite from the database/server memory
    global dbClient
    db = dbClient[server.displayName]
    collection = db["invites"]
    dict = vars(usedInvite)
    collection.delete_one(dict)

    server.invites.remove(usedInvite)    

#### Commands ####

#default format for commands, where the function name is the command to type
@bot.command()
@commands.has_role('admin')
async def test(ctx, *args):
    #send the arguments of the command back to the user
    await ctx.send(' '.join(args))

#just to forcibly check for forum responses
@bot.command()
async def forceCheck(ctx, *args):

    if(not hasPermission(ctx,"admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    responses = checkForum(getServer(ctx),True)
    if(responses <= 0):
        await ctx.send("There are no new form responses.")
    else:
        await ctx.send("There are `" + str(responses) + "` new form responses.")

@bot.command()
async def handleResponses(ctx, *args):

    if(not hasPermission(ctx,"admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    responses = checkForum(getServer(ctx),True)
    if(responses <= 0):
        await ctx.send("There are no new form responses.")
    else:
        await ctx.send("Generating emails/invites...")

        #open the responses spread-sheet
        scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)
        responsesSheet = client.open("Responses to discord signup").sheet1

        emails = responsesSheet.col_values(3)
        index = len(responsesSheet.col_values(8)) + 1 #the index of the first new response
        flaggedResponses = []
        validResponses = []

        for i in range(responses):
            currentIndex = index + i 
            response = responsesSheet.row_values(currentIndex)
            flagged = False
            #check if this is a duplicate response or if it uses an invalid email
            for j in range(currentIndex - 1):
                if(response[2] == emails[j] or not response[2].endswith("@myumanitoba.ca")):
                    flaggedResponses.append(response)
                    flagged = True
                    break
            if(not flagged):
                validResponses.append(response)

        server = getServer(ctx)
        guild = discord.utils.get(bot.guilds, name=server.displayName)
        inviteChannel = discord.utils.get(guild.channels, name="introductions")
        global dbClient
        if(server.displayName == "UManitoba Computer Science Lounge"):
            db = dbClient["csDiscord"]
        else:
            db = dbClient[server.displayName]
        collection = db["invites"]
        global formattedEmails

        for response in validResponses:
            #generate an invite link
            newInvite = await inviteChannel.create_invite(max_uses=5, unique=True, reason="Created invite for user: " + response[4])
            #generate a utils link to be saved server side
            roles = response[5].split(", ")
            roles.append(response[4])
            invite = utils.Invite(newInvite.url,0,server.displayName,roles)
            server.invites.append(invite)
            #add it to the database
            dict = vars(invite)
            collection.insert_one(dict)

            firstName = response[1].split(" ")[0].lower().capitalize()
            formattedEmails.append(utils.Email(response[2],firstName,invite.url))

        if(len(validResponses) > 0):
            await ctx.send("Emails generated, use `.previewEmails` to preview.")
            if(len(flaggedResponses) > 0):
                await ctx.send("`" + str(len(flaggedResponses)) + "` invalid responses found.")
        else:
            await ctx.send("No valid responses found, no emails/invites were generated.")

@bot.command()
async def previewEmails(ctx, *args):
    global formattedEmails

    if(not hasPermission(ctx,"admin")):
        await ctx.send("Error: You do not have permission to use this command.")
        return

    if(len(formattedEmails) != 0):
        await ctx.send("Printing out formatted emails:")
        for email in formattedEmails:
            await ctx.send(str(email))
    else:
        await ctx.send("No emails to preview.")

@bot.command()
async def iam(ctx, *args):

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
                        await ctx.send("`" + year + "` role added.")
                else:
                    await ctx.send("Error: Correct format is `" + PREFIX + "iam " + args[0] + " year`.")
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
                        await ctx.send("Year role `" + role.name + "` removed.")
                    else:
                        await ctx.send("Error: You do not have the role `" + role.name + "`.")
                else:
                    await ctx.send("Error: Correct format is `" + PREFIX + "iamn " + args[0] + " year`.")
            else:
                await ctx.send("Error: Year or colour role `" + args[0] + "` not found.")
        else:
            await ctx.send("Error: Year or colour role must be specified")
    else:
        await ctx.send("Error: You do not have permission to use this command.")

@bot.command()
async def colour(ctx, *args):
    server = getServer(ctx)
    global dbClient
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
async def notify(ctx, *args):
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
       
@bot.command()
async def autoassignrole(ctx,*args):
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

## Fun commands
@bot.command()
async def sendmessage(ctx, *, arg): 
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

#for future me
'''
#should play a random yelling sound effect in voice chat
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.command()
async def exams(ctx,*args):
    guild = discord.utils.get(bot.guilds, name="UManitoba Computer Science Lounge")
    voice_channel = discord.utils.get(guild.voice_channels, name="scream-into-the-void")

    links = ['https://youtu.be/9M3NqnPhlSQ','https://youtu.be/SiMsRJpd-VA','https://youtu.be/-_ZNxsiIqgA']
    url = links[random.randint(0,2)]

    vc = await voice_channel.connect()

    player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
    vc.play(player, after=await vc.disconnect())

'''
bot.run(TOKEN)

