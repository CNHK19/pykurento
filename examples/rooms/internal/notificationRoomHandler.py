import simplejson
from .protocolElements import ProtocolElements


class NotificationRoomHandler():

    def __init__(self, notifService):
        self.notifService = notifService

    def onRoomClosed(self, roomName, participants):
        notifParams = dict()

        notifParams[ProtocolElements.ROOMCLOSED_ROOM_PARAM]=roomName

        for participant in participants:
            self.notifService.sendNotification(participant.getParticipantId(), ProtocolElements.ROOMCLOSED_METHOD,
                              notifParams)


    def onParticipantJoined(self, request, roomName, newUserName, existingParticipants, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        result = []
        for participant in existingParticipants:
            participantJson = dict()
            participantJson[ProtocolElements.JOINROOM_PEERID_PARAM] = participant.getUserName()

            if participant.isStreaming():
                stream = dict()
                stream[ProtocolElements.JOINROOM_PEERSTREAMID_PARAM] = "webcam"
                streamsArray = []
                streamsArray.append(stream)
                participantJson[ProtocolElements.JOINROOM_PEERSTREAMS_PARAM] = streamsArray

            result.append(participantJson)

            notifParams = dict()

            notifParams[ProtocolElements.PARTICIPANTJOINED_USER_PARAM] = newUserName

            self.notifService.sendNotification(participant.getParticipantId(),
                                          ProtocolElements.PARTICIPANTJOINED_METHOD, notifParams)

        result = simplejson.dumps(result)
        self.notifService.sendResponse(request, result)

    def onParticipantLeft(self, request, userName, remainingParticipants, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        params = dict()
        params[ProtocolElements.PARTICIPANTLEFT_NAME_PARAM] = userName

        for participant in remainingParticipants:
            self.notifService.sendNotification(participant.getParticipantId(), ProtocolElements.PARTICIPANTLEFT_METHOD,
                              params)

        self.notifService.sendResponse(request, simplejson.dumps(dict()))
        self.notifService.closeSession(request)


    def onPublishMedia(self, request, publisherName, sdpAnswer, participants, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        result = dict()
        result[ProtocolElements.PUBLISHVIDEO_SDPANSWER_PARAM] = sdpAnswer
        result = simplejson.dumps(result)
        self.notifService.sendResponse(request, result)

        params = dict()
        params[ProtocolElements.PARTICIPANTPUBLISHED_USER_PARAM] = publisherName

        stream = dict()
        stream[ProtocolElements.PARTICIPANTPUBLISHED_STREAMID_PARAM] = "webcam"

        streamsArray = []
        streamsArray.append(stream)

        params[ProtocolElements.PARTICIPANTPUBLISHED_STREAMS_PARAM] = streamsArray

        for participant in participants:
            if participant.getParticipantId() == request.getParticipantId():
                continue
            else:
                self.notifService.sendNotification(participant.getParticipantId(),
                                              ProtocolElements.PARTICIPANTPUBLISHED_METHOD, params)


    def onUnpublishMedia(self, request, publisherName, participants, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        self.notifService.sendResponse(request, simplejson.dumps(dict()))

        params = dict()
        params[ProtocolElements.PARTICIPANTUNPUBLISHED_NAME_PARAM] = publisherName

        for participant in participants:
            if participant.getParticipantId()==request.getParticipantId():
                continue
            else:
                self.notifService.sendNotification(participant.getParticipantId(),
                                                   ProtocolElements.PARTICIPANTUNPUBLISHED_METHOD, params)

    def onSubscribe(self, request, sdpAnswer, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        result = dict()
        result[ProtocolElements.RECEIVEVIDEO_SDPANSWER_PARAM] = sdpAnswer
        result = simplejson.dumps(result)

        self.notifService.sendResponse(request, result)


    def onUnsubscribe(self, request, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        self.notifService.sendResponse(request, simplejson.dumps(dict()))

    def onSendMessage(self, request, message, userName, roomName, participants, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        self.notifService.sendResponse(request, simplejson.dumps(dict()))

        params = dict()
        params[ProtocolElements.PARTICIPANTSENDMESSAGE_ROOM_PARAM] = roomName
        params[ProtocolElements.PARTICIPANTSENDMESSAGE_USER_PARAM] = userName
        params[ProtocolElements.PARTICIPANTSENDMESSAGE_MESSAGE_PARAM] = message


        for participant in participants:
            self.notifService.sendNotification(participant.getParticipantId(),ProtocolElements.PARTICIPANTSENDMESSAGE_METHOD, params)


    def onPaintSend(self, request, userName, coordinates, windowSize, brushColor, brushSize, brushType, roomName, participants, error):
        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        self.notifService.sendResponse(request, simplejson.dumps(dict()))

        params = dict()
        params[ProtocolElements.ONPAINTSEND_ROOM_PARAM] = roomName
        params[ProtocolElements.ONPAINTSEND_USER_PARAM] = userName
        params[ProtocolElements.ONPAINTSEND_COORDS_PARAM] = coordinates
        params[ProtocolElements.ONPAINTSEND_DISPLAY_SIZE_PARAM] = windowSize
        params[ProtocolElements.ONPAINTSEND_BRUSH_SIZE_PARAM] = brushSize
        params[ProtocolElements.ONPAINTSEND_BRUSH_COLOR_PARAM] = brushColor
        params[ProtocolElements.ONPAINTSEND_BRUSH_TYPE_PARAM] = brushType


        for participant in participants:
            self.notifService.sendNotification(participant.getParticipantId(),ProtocolElements.ONPAINTSEND_METHOD, params)


    def onStopSessionRecording(self, request, error):

        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return
        else:
            self.notifService.sendResponse(request, simplejson.dumps(dict()))

    def onSessionRecording(self, request, error):

        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return
        else:
            self.notifService.sendResponse(request, simplejson.dumps(dict()))

    def onRecvIceCandidate(self, request, error):

        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return
        else:
            self.notifService.sendResponse(request, simplejson.dumps(dict()))

    def onParticipantEvicted(self, participant):
        self.notifService.sendNotification(participant.getParticipantId(),
        ProtocolElements.PARTICIPANTEVICTED_METHOD, simplejson.dumps(dict()))

    def onIceCandidate(self, roomName, participantId, endpointName, candidate, sdpMLineIndex, sdpMid):
        params = dict()
        params[ProtocolElements.ICECANDIDATE_EPNAME_PARAM] = endpointName
        params[ProtocolElements.ICECANDIDATE_SDPMLINEINDEX_PARAM] = sdpMLineIndex
        params[ProtocolElements.ICECANDIDATE_SDPMID_PARAM] = sdpMid
        params[ProtocolElements.ICECANDIDATE_CANDIDATE_PARAM] = candidate

        self.notifService.sendNotification(participantId, ProtocolElements.ICECANDIDATE_METHOD, params)

    def onPipelineError(self, roomName, participantIds, description):
        notifParams = dict()
        notifParams[ProtocolElements.MEDIAERROR_ERROR_PARAM] = description

        for pid in participantIds:
            self.notifService.sendNotification(pid, ProtocolElements.MEDIAERROR_METHOD, notifParams)

    def onMediaElementError(self, roomName, participantId, description):
        notifParams = dict()
        notifParams[ProtocolElements.MEDIAERROR_ERROR_PARAM] = description

        self.notifService.sendNotification(participantId, ProtocolElements.MEDIAERROR_METHOD, notifParams)

    #todo
    def onCall(self, request, sdpAnswer, error):

        if error:
            self.notifService.sendErrorResponse(request, None, error)
            return

        result = dict()
        result[ProtocolElements.RECEIVEVIDEO_SDPANSWER_PARAM] = sdpAnswer
        result = simplejson.dumps(result)

        self.notifService.sendResponse(request, result)

    def updateFilter(self, roomName, participant, filterId, state):
        pass

    def getNextFilterState(self, filterId, state):
        return None
