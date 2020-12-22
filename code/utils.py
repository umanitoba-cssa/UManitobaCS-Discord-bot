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

        self.autoAssign = True
        self.greetMessage = ""

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
    def __init__(self, url, server, roles, isEventRole):
        self.url = url
        self.uses = 0
        self.server = server
        self.autoAssignRoles = roles
        self.isEventRole = isEventRole