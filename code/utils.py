#Classes/objects for the bot

#data I want to store locally about servers 
class Server:
    def __init__(self, displayName):
        self.displayName = displayName

        #lists
        self.colourRoles = []
        self.defaultRoles = []
        self.execRoles = []
        self.announcementRoles = []
        self.yearRoles = []
        self.adminRoles = []
        self.invites = []

        self.autoAssign = True
        self.greetMessage = ""
        self.formLastChecked = 0

    def __str__(self):
        return self.displayName

    def lowerRoleList(self):
        returnList = []
        for x in self.defaultRoles:
            returnList.append(x.lower())
        for x in self.execRoles:
            returnList.append(x.lower())
        for x in self.announcementRoles:
            returnList.append(x.lower())
        for x in self.adminRoles:
            returnList.append(x.lower())
        return returnList

class Invite:
    def __init__(self, url, uses, server, roles):
        self.url = url
        self.uses = uses
        self.server = server #display name
        self.autoAssignRoles = roles

class Email:
    def __init__(self, recipient, name, inviteUrl):
        self.recipient = recipient

        self.subject = "UManitoba Computer Science Discord Invitation"
        template = open("templates/template_html.txt","r").read()
        self.body = template.format(name = name, invite = inviteUrl)
        self.inviteUrl = inviteUrl
        self.previewMessage = ""
        self.previewer = ""

    def __str__(self):
        return "```html\nTO:\n" + self.recipient + "\nSUBJECT:\n" + self.subject + "\nBODY:\n" + self.body + "```"

class UserHistory:
    def __init__(self, id, username, nickname):
        self.id = id
        self.usernames = []
        self.nicknames = []

        self.usernames.append(username)
        self.nicknames.append(nickname)

    def __str__(self):
        return "```\n**ID:** " + self.id + "\n**Usernames:**\n" + ", ".join(self.usernames) + "\n**Nicknames:**\n" + ", ".join(self.nicknames) + "```"