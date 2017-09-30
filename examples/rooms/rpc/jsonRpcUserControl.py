
from ..internal.protocolElements import ProtocolElements
from .participantSession import SESSION_KEY, ParticipantSession

class JsonRpcUserControl():

    def __init__(self, roomManager):
        self.roomManager = roomManager

    @staticmethod
    def getStringParam(request, key):
        if not request or key not in request.keys():
            raise("Request element '" + key + "' is missing")

        return str(request.get(key))

    @staticmethod
    def getIntParam(request, key):
        if not request or key not in request.keys():
            raise("Request element '" + key + "' is missing")

        return int(request.get(key))

    @staticmethod
    def getBooleanParam(request, key):
        if not request or key not in request.keys():
            raise("Request element '" + key + "' is missing")

        return bool(request.get(key))


    def getParticipantSession(self, transaction):
        pass
        # session = transaction.getSession()
        # participantSession = session.getAttributes().get(ParticipantSession.SESSION_KEY)
        # if not participantSession:
        #     participantSession = ParticipantSession(None,None)
        #     # session.getAttributes()[SESSION_KEY] = participantSession
        #     session.getAttributes()[ParticipantSession.SESSION_KEY] = participantSession
        #
        # return participantSession

    def joinRoom(self, transaction, request, participantRequest):

        roomName = self.getStringParam(request, ProtocolElements.JOINROOM_ROOM_PARAM)
        userName = self.getStringParam(request, ProtocolElements.JOINROOM_USER_PARAM)

        dataChannels = False

        if ProtocolElements.JOINROOM_DATACHANNELS_PARAM in request.keys():
            print(request[ProtocolElements.JOINROOM_DATACHANNELS_PARAM])

            # dataChannels = bool(request.getParams().get(ProtocolElements.JOINROOM_DATACHANNELS_PARAM))


        self.roomManager.joinRoom(userName, roomName, dataChannels, True, participantRequest)


    def publishVideo(self, transaction, request, participantRequest):
        sdpOffer = self.getStringParam(request, ProtocolElements.PUBLISHVIDEO_SDPOFFER_PARAM)
        doLoopback = self.getBooleanParam(request, ProtocolElements.PUBLISHVIDEO_DOLOOPBACK_PARAM)


        self.roomManager.publishMedia(participantRequest, sdpOffer, doLoopback)

    def unpublishVideo(self, transaction, request, participantRequest):
        self.roomManager.unpublishMedia(participantRequest)

    def receiveVideoFrom(self, transaction, request, participantRequest):
        senderName = self.getStringParam(request, ProtocolElements.RECEIVEVIDEO_SENDER_PARAM)
        senderName = senderName[0:senderName.rfind("_")]

        sdpOffer = self.getStringParam(request, ProtocolElements.RECEIVEVIDEO_SDPOFFER_PARAM)

        self.roomManager.subscribe(senderName, sdpOffer, participantRequest)

    def unsubscribeFromVideo(self, transaction, request, participantRequest):
        senderName = self.getStringParam(request, ProtocolElements.UNSUBSCRIBEFROMVIDEO_SENDER_PARAM)
        senderName = senderName[0:senderName.rfind("_")]

        self.roomManager.unsubscribe(senderName, participantRequest)

    def leaveRoomAfterConnClosed(self, sessionId):
        try:
            self.roomManager.evictParticipant(sessionId)
            print("Evicted participant with sessionId {%s}" % sessionId)
        except:
            print("Unable to evict: {%s}" % sessionId)

    def leaveRoom(self, transaction, request, participantRequest):
        exists = False
        pid = participantRequest.getParticipantId()

        # trying with room info from session
        roomName = None
        if transaction:
            # participant = self.roomManager.getParticipant(pid)
            # room = participant.getRoom()
            roomName = self.roomManager.internalManager.getRoomName(pid)

        if not roomName: # null when afterConnectionClosed
            print("No room information found for participant with session Id {%s}. Using the admin method to evict the user." % pid)
            self.leaveRoomAfterConnClosed(pid)
        else:
            # sanity check, don't call leaveRoom unless the id checks out
            for part in self.roomManager.getParticipants(roomName):
                if part.getParticipantId() == participantRequest.getParticipantId():
                    exists = True
                    break

            if exists:
                print("Participant with sessionId {%s} is leaving room {%s}" % (pid, roomName))
                self.roomManager.leaveRoom(participantRequest)
                print("Participant with sessionId {%s} has left room {%s}" % (pid, roomName))
            else:
                print("Participant with session Id {%s} not found in room {%s}. Using the admin method to evict the user." % (pid, roomName))
                self.leaveRoomAfterConnClosed(pid)

    def onIceCandidate(self, transaction, request, participantRequest):
        endpointName = self.getStringParam(request, ProtocolElements.ONICECANDIDATE_EPNAME_PARAM)
        candidate = self.getStringParam(request, ProtocolElements.ONICECANDIDATE_CANDIDATE_PARAM)
        sdpMid = self.getStringParam(request, ProtocolElements.ONICECANDIDATE_SDPMIDPARAM)
        sdpMLineIndex = self.getIntParam(request, ProtocolElements.ONICECANDIDATE_SDPMLINEINDEX_PARAM)
        self.roomManager.onIceCandidate(endpointName, candidate, sdpMLineIndex, sdpMid, participantRequest)


    def sendMessage(self, transaction, request, participantRequest):
        userName = self.getStringParam(request, ProtocolElements.SENDMESSAGE_USER_PARAM)
        roomName = self.getStringParam(request, ProtocolElements.SENDMESSAGE_ROOM_PARAM)
        message = self.getStringParam(request, ProtocolElements.SENDMESSAGE_MESSAGE_PARAM)

        print("Message from {%s} in room {%s}: '{%s}'" % userName, roomName, message)

        self.roomManager.sendMessage(message, userName, roomName, participantRequest)

    def paintSend(self, transaction, request, participantRequest):
        userName = self.getStringParam(request, ProtocolElements.ONPAINTSEND_USER_PARAM)
        roomName = self.getStringParam(request, ProtocolElements.ONPAINTSEND_ROOM_PARAM)
        coordinates = self.getStringParam(request, ProtocolElements.ONPAINTSEND_COORDS_PARAM)
        windowSize = self.getStringParam(request, ProtocolElements.ONPAINTSEND_DISPLAY_SIZE_PARAM)
        brushSize = self.getStringParam(request, ProtocolElements.ONPAINTSEND_BRUSH_SIZE_PARAM)
        brushColor = self.getStringParam(request, ProtocolElements.ONPAINTSEND_BRUSH_COLOR_PARAM)
        brushType = self.getStringParam(request, ProtocolElements.ONPAINTSEND_BRUSH_TYPE_PARAM)

        self.roomManager.sendPaint(userName, coordinates, windowSize, brushColor, brushSize, brushType, roomName, participantRequest)


    def recordSession(self, transaction, request, participantRequest):
        record = self.getStringParam(request, ProtocolElements.RECORD_SESSION_PARAM)
        room = self.getStringParam(request, ProtocolElements.RECORD_ROOM_PARAM)

        self.roomManager.recordSession(room, record, participantRequest)

    def customRequest(self, transaction, request, participantRequest):
        print("Unsupported method: customRequest")
        #todo
        pass


    def register(self, transaction, request,  participantRequest):
        name = self.getStringParam(request, ProtocolElements.JOINROOM_REGISTER_NAME)


    def call(self, transaction, request,  participantRequest):
        senderName = self.getStringParam(request, ProtocolElements.CALL_SENDER_PARAM)
        senderName = senderName[0:senderName.rfind("_")]
        toName = self.getStringParam(request, ProtocolElements.CALL_TO_PARAM)
        sdpOffer = self.getStringParam(request, ProtocolElements.CALL_SDPOFFER_PARAM)

        self.roomManager.call(senderName, toName,sdpOffer, participantRequest)



    def getIceCandidates(self, transaction, request, participantRequest):
        self.roomManager.getherCandidates(participantRequest)
