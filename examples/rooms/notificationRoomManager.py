from .internal.notificationRoomHandler import NotificationRoomHandler
from .internal.defaultKurentoClientSessionInfo import DefaultKurentoClientSessionInfo
from .roomManager import RoomManager
from .exception.roomException import Code, RoomException


class NotificationRoomManager():

    def __init__(self, notificationService, kcProvider):
        self.notificationRoomHandler = NotificationRoomHandler(notificationService)
        self.internalManager = RoomManager(self.notificationRoomHandler, kcProvider)


    def joinRoom(self, userName, roomName, dataChannels, webParticipant, request):

        print("Request [JOIN_ROOM] user={%s}, room={%s}, web={%s}" %
              (userName, roomName,str(webParticipant) ))

        existingParticipants = None

        try:
            kcSessionInfo = DefaultKurentoClientSessionInfo(request.getParticipantId(), roomName)
            existingParticipants = self.internalManager.joinRoom(userName, roomName, dataChannels, webParticipant, kcSessionInfo,
                  request.getParticipantId())
        except Exception as e:
            print("PARTICIPANT {%s}: Error joining/creating room {%s}: %s" % (userName, roomName, str(e)))

            self.notificationRoomHandler.onParticipantJoined(request, roomName, userName, None, True)

        # if existingParticipants:
        self.notificationRoomHandler.onParticipantJoined(request, roomName, userName, existingParticipants, None)


    def leaveRoom(self, request):
        pid = request.getParticipantId()
        remainingParticipants = dict()
        roomName = ""
        userName = ""

        try:
            roomName = self.internalManager.getRoomName(pid)
            userName = self.internalManager.getParticipantName(pid)
            remainingParticipants = self.internalManager.leaveRoom(pid)
        except Exception as e:
            print("PARTICIPANT {%s}: Error leaving room {%s}: %s" % (userName, roomName, str(e)))
            self.notificationRoomHandler.onParticipantLeft(request, None, None, True)

        if remainingParticipants:
            self.notificationRoomHandler.onParticipantJoined(request, roomName, userName, remainingParticipants, None)


    def publishMedia(self, request, sdp, doLoopback, isOffer=True, loopbackAlternativeSrc=None, loopbackConnectionType=None, mediaElements=[]):
        pid = request.getParticipantId()
        userName = ""
        participants = []
        sdpAnswer = ""

        #todo
        # try:
        userName = self.internalManager.getParticipantName(pid)
        sdpAnswer = self.internalManager.publishMedia(request.getParticipantId(), sdp, doLoopback, isOffer,  loopbackAlternativeSrc,
                  loopbackConnectionType,  mediaElements)
        participants = self.internalManager.getParticipants(self.internalManager.getRoomName(pid))
        # except:
        #     print("PARTICIPANT {%s}: Error publishing media" % userName)
        #     self.notificationRoomHandler.onPublishMedia(request, None, None, None, True)

        if sdpAnswer:
            self.notificationRoomHandler.onPublishMedia(request, userName, sdpAnswer, participants, None)


    def unpublishMedia(self, request):
        pid = request.getParticipantId()
        userName = ""
        participants = []
        unpublished = False

        try:
            userName = self.internalManager.getParticipantName(pid)
            self.internalManager.unpublishMedia(pid)
            unpublished = True
            participants = self.internalManager.getParticipants(self.internalManager.getRoomName(pid))
        except:
            print("PARTICIPANT {%s}: Error unpublishing media" % userName)
            self.notificationRoomHandler.onUnpublishMedia(request, None, None, True)

        if unpublished:
            self.notificationRoomHandler.onUnpublishMedia(request, userName, participants, None)


    def subscribe(self, remoteName, sdpOffer, request):
        pid = request.getParticipantId()
        userName = None
        sdpAnswer = None

        #todo
        # try:
        userName = self.internalManager.getParticipantName(pid)
        sdpAnswer = self.internalManager.subscribe(remoteName, sdpOffer, pid)
        # except Except as e:
        #     print("PARTICIPANT {%s}: Error subscribing to {%s}" % (userName, remoteName))
        #     self.notificationRoomHandler.onSubscribe(request, None, True)

        if sdpAnswer:
            self.notificationRoomHandler.onSubscribe(request, sdpAnswer, None)


    def unsubscribe(self, remoteName, request):

        pid = request.getParticipantId()
        userName = None
        unsubscribed = False

        try:
            userName = self.internalManager.getParticipantName(pid)
            self.internalManager.unsubscribe(remoteName, pid)
            unsubscribed = True

        except:
            print("PARTICIPANT {%s}: Error unsubscribing from {%s}" % userName, remoteName)
            self.notificationRoomHandler.onUnsubscribe(request, True)

        if unsubscribed:
            self.notificationRoomHandler.onUnsubscribe(request, None)

    def onIceCandidate(self, endpointName, candidate, sdpMLineIndex, sdpMid, request):
        pid = request.getParticipantId()
        userName = ""
        #todo
        # try:
        userName = self.internalManager.getParticipantName(pid)
        self.internalManager.onIceCandidate(endpointName, candidate, sdpMLineIndex, sdpMid, request.getParticipantId())
        self.notificationRoomHandler.onRecvIceCandidate(request, None)
        #
        # except Exception as e:
        #     print("PARTICIPANT {%s}: Error receiving ICE candidate (epName={%s}, candidate={%s}: %s)" %
        #           (userName, endpointName, candidate, str(e)))
        #     self.notificationRoomHandler.onRecvIceCandidate(request, True)

    def getherCandidates(self, request):
        pid = request.getParticipantId()
        self.internalManager.getherCandidates(pid)


    def sendMessage(self, message, userName, roomName, request):
        print("Request [SEND_MESSAGE] message={%s} ({%s})" % (message, request))

        try:
            if userName == self.internalManager.getParticipantName(request.getParticipantId()):
                raise(Code.USER_NOT_FOUND_ERROR_CODE, "Provided username '" + userName + "' differs from the participant's name")
            if roomName != self.internalManager.getRoomName(request.getParticipantId()):
                raise(Code.ROOM_NOT_FOUND_ERROR_CODE, "Provided room name '" + roomName + "' differs from the participant's room")
            self.notificationRoomHandler.onSendMessage(request, message, userName, roomName, self.internalManager.getParticipants(roomName), None)
        except:
            print ("PARTICIPANT {%s}: Error sending message" % userName)
            self.notificationRoomHandler.onSendMessage(request, None, None, None, None, True)


    def sendPaint(self, userName, coordinates, windowSize, brushColor, brushSize, brushType, roomName, request):

        try:
            if self.internalManager.getRoomName(request.getParticipantId()) != roomName:
                raise(Code.ROOM_NOT_FOUND_ERROR_CODE, "Provided room name '" + roomName+ "' differs from the participant's room")

            self.notificationRoomHandler.onPaintSend(request, userName, coordinates, windowSize, brushColor,
	    		  brushSize, brushType, roomName, self.internalManager.getParticipants(roomName), None)
            if self.internalManager.isPublisherRecording(request.getParticipantId()):
                self.internalManager.saveCoordToFile(request.getParticipantId(), coordinates, windowSize,brushColor, brushSize, brushType)

        except Exception as e:
            print("PARTICIPANT {}: Error sending message", str(e))
            self.notificationRoomHandler.onPaintSend(request, None, None, None, None, None, None,None, None, True)

    def recordSession(self, roomName, record, participantRequest):
        recordSession = bool(record)
        if recordSession:
            if self.internalManager.isPublisherRecording(participantRequest.getParticipantId()):
                print("PARTICIPANT {}: Session is recordered")

            else:
                existingParticipant = []

                try:
                    existingParticipant = self.internalManager.recordSession(roomName, participantRequest.getParticipantId())
                except:
                    print("PARTICIPANT {}: Error recording session")

                if existingParticipant:
                    self.notificationRoomHandler.onSessionRecording(participantRequest, None)

        else:
            if not self.internalManager.isPublisherRecording(participantRequest.getParticipantId()):
                print("PARTICIPANT {}: Session is not recordered")
            else:
                existingParticipant = []
                try:
                    existingParticipant = self.internalManager.stopRecording(roomName,
                                                                        participantRequest.getParticipantId())
                except:
                    print("PARTICIPANT {}: Error stop recording")

                if existingParticipant:
                    self.notificationRoomHandler.onStopSessionRecording(participantRequest, None)


    def call(self, senderName, toName, sdpOffer, request):
        print("Request [call] senderName={%s} toName={%s} sdpOffer={%s}" % (senderName, toName, sdpOffer))

        pid = request.getParticipantId()
        userName = None
        sdpAnswer = None

        #todo
        if 1:
            userName = self.internalManager.getParticipantName(pid)
            sdpAnswer = self.internalManager.call(userName, toName, sdpOffer)
        # except:
        #     print("PARTICIPANT {%s}: Error call to {%s}" % (userName, toName))
        #     self.notificationRoomHandler.onCall(request, None, True)

        if sdpAnswer:
            self.notificationRoomHandler.onCall(request, sdpAnswer, None)


    def close(self):
        if not self.internalManager.isClosed():
            self.internalManager.close()

    def getRooms(self):
        return self.internalManager.getRooms()

    def getParticipants(self, roomName):
        return self.internalManager.getParticipants(roomName)

    def getPublishers(self, roomName):
        return self.internalManager.getPublishers(roomName)

    def getSubscribers(self, roomName):
        return self.internalManager.getSubscribers(roomName)

    def getPeerPublishers(self, participantId):
        return self.internalManager.getPeerPublishers(participantId)

    def getPeerSubscribers(self, participantId):
        return self.internalManager.getPeerSubscribers(participantId)

    def createRoom(self, kcSessionInfo):
        return self.internalManager.createRoom(kcSessionInfo)

    def getPipeline(self, participantId):
        return self.internalManager.getPipeline(participantId)

    def evictParticipant(self, participantId):

        participant = self.internalManager.getParticipantInfo(participantId)
        remainingParticipants = self.internalManager.leaveRoom(participantId)
        self.notificationRoomHandler.onParticipantLeft(participant.getUserName(), remainingParticipants)
        self.notificationRoomHandler.onParticipantEvicted(participant)

    def closeRoom(self, roomName):
        participants = self.internalManager.closeRoom(roomName)
        self.notificationRoomHandler.onRoomClosed(roomName, participants)

    def generatePublishOffer(self, participantId):
        self.internalManager.generatePublishOffer(participantId)

    def addMediaElement(self, participantId, element, type=None):
        self.internalManager.addMediaElement(participantId, element, type)

    def mutePublishedMedia(self, muteType, participantId):
        self.internalManager.mutePublishedMedia(muteType, participantId)

    def unmutePublishedMedia(self, participantId):
        self.internalManager.unmutePublishedMedia(participantId)

    def muteSubscribedMedia(self, remoteName, muteType, participantId):
        self.internalManager.muteSubscribedMedia(remoteName, muteType, participantId)

    def unmuteSubscribedMedia(self, remoteName, participantId):
        self.internalManager.unmuteSubscribedMedia(remoteName, participantId)

    def getRoomManager(self):
        return self.internalManager

    def updateFilter(self, roomId, filterId):
        self.internalManager.updateFilter(roomId, filterId)
