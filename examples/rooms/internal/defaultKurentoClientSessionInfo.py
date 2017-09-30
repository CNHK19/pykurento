
class DefaultKurentoClientSessionInfo():

    def __init__(self, participantId, roomName):
        self.participantId = participantId
        self.roomName = roomName

    def getParticipantId(self):
        return self.participantId

    def setParticipantId(self, participantId):
        self.participantId = participantId

    def getRoomName(self):
        return self.roomName

    def setRoomName(self, roomName):
        self.roomName = roomName