

class ParticipantRequest():

    def __init__(self, participantId, requestId):
        self.requestId = requestId
        self.participantId = participantId

    def getRequestId(self):
        return self.requestId

    def setRequestId(self, id):
        self.requestId = id

    def getParticipantId(self):
        return self.participantId

    def setParticipantId(self, participantId):
        self.participantId = participantId