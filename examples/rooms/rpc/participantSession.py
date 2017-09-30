
SESSION_KEY = "participant"

class ParticipantSession():
    SESSION_KEY = "participant"

    def __init__(self, participantName, roomName):
        self.participantName = participantName
        self.roomName = roomName
        self.dataChannels = False

    def getParticipantName(self):
        return self.participantName

    def setParticipantName(self, participantName):
        self.participantName = participantName

    def getRoomName(self):
        return self.roomName

    def setRoomName(self, roomName):
        self.roomName = roomName

    def useDataChannels(self):
        return self.dataChannels

    def setDataChannels(self, dataChannels):
        self.dataChannels = dataChannels

    def toString(self):
        builder = "["
        if self.participantName:
            builder += "participantName=" + self.participantName + ", "

        if self.roomName:
            builder += "roomName=" + self.roomName + ", "

        builder += "useDataChannels=" + str(self.dataChannels) + "]"

        return builder