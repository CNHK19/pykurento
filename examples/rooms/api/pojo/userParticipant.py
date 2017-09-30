

class UserParticipant():

    def __init__(self, participantId, userName, streaming=None):
        self.participantId = participantId
        self.userName = userName
        self.streaming = streaming

    def getParticipantId(self):
        return self.participantId

    def setParticipantId(self, participantId):
        self.participantId = participantId

    def getUserName(self):
        return self.userName

    def setUserName(self, userName):
        self.userName = userName

    def isStreaming(self):
        return self.streaming

    def setStreaming(self,streaming):
        self.streaming = streaming