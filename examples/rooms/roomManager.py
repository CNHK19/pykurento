from .exception.roomException import Code, RoomException
from .endpoint.sdpType import SdpType
from .internal.room import Room
from .api.pojo.userParticipant import UserParticipant
from pykurento.client import IceCandidate
from pykurento.helper import timing
import time


class RoomManager():

    def __init__(self, roomHandler, kcProvider):
        self.roomHandler = roomHandler
        self.kcProvider = kcProvider

        self.rooms = dict()
        self.closed = False
        # self.ice_candidates = []

    def joinRoom(self, userName, roomName, dataChannels, webParticipant, kcSessionInfo, participantId):

        print("Request [JOIN_ROOM] user={%s}, room={%s}, web={%s} kcSessionInfo.room={%s} ({%s})" %
              (userName, roomName, str(webParticipant), kcSessionInfo.getRoomName() if kcSessionInfo else "", participantId))

        room = self.rooms.get(roomName)
        if not room and kcSessionInfo:
            self.createRoom(kcSessionInfo)

        room = self.rooms.get(roomName)
        if not room:
            print("Room '{%s}' not found" % roomName)
            raise RoomException("Room '" + roomName + "' was not found, must be created before '" + userName + "' can join", Code.ROOM_NOT_FOUND_ERROR_CODE)

        if room.isClosed():

            print("'{%s}' is trying to join room '{%s}' but it is closing" % (userName, roomName))
            raise RoomException("'" + userName + "' is trying to join room '" + roomName + "' but it is closing", Code.ROOM_CLOSED_ERROR_CODE)

        existingParticipants = self.getParticipants(roomName)
        room.join(participantId, userName, dataChannels, webParticipant)
        return existingParticipants

    def leaveRoom(self, participantId):
        print("Request [LEAVE_ROOM] ({%s})" % participantId)
        participant = self.getParticipant(participantId)
        room = participant.getRoom()
        roomName = room.getName()

        if room.isClosed():
            print("'{%s}' is trying to leave room '{%s}' but it is closing" % (participant.getName(), roomName))
            raise RoomException("'" + participant.getName() + "' is trying to leave room '" + roomName + "' but it is closing", Code.ROOM_CLOSED_ERROR_CODE)

        room.leave(participantId)
        remainingParticipants = None
        try:
            remainingParticipants = self.getParticipants(roomName)
        except:
            print("Possible collision when closing the room '{}' (not found)")
            remainingParticipants = remainingParticipants.clear()

        if not remainingParticipants:
            print("No more participants in room '{%s}', removing it and closing it" % roomName)
            room.close()
            del self.rooms[roomName]
            print("Room '{%s}' removed and closed" % roomName)

        return remainingParticipants

    @timing
    def publishMedia(self, participantId, sdp, doLoopback, isOffer=True, loopbackAlternativeSrc=None,  loopbackConnectionType=None,  mediaElements=[]):
        print("Request [PUBLISH_MEDIA] isOffer={%s} sdp={%s} loopbackAltSrc={%s} lpbkConnType={%s} doLoopback={%s} mediaElements={%s} ({%s})" % (isOffer, sdp,
                  bool(loopbackAlternativeSrc == None), loopbackConnectionType, doLoopback, mediaElements, participantId))

        sdpType = SdpType.OFFER if isOffer else SdpType.ANSWER
        participant = self.getParticipant(participantId)
        name = participant.getName()
        room = participant.getRoom()

        participant.createPublishingEndpoint()
        for elem in mediaElements:
            participant.getPublisher().apply(elem)

        sdpResponse = participant.publishToRoom(sdpType, sdp, doLoopback, loopbackAlternativeSrc, loopbackConnectionType)

        if not sdpResponse:
            raise RoomException("Error generating SDP response for publishing user " + name, Code.MEDIA_SDP_ERROR_CODE)

        room.newPublisher(participant)
        return sdpResponse

    def generatePublishOffer(self, participantId):
        print("Request [GET_PUBLISH_SDP_OFFER] ({%d})" % participantId)

        participant = self.getParticipant(participantId)
        name = participant.getName()
        room = participant.getRoom()

        participant.createPublishingEndpoint()

        sdpOffer = participant.preparePublishConnection()
        if not sdpOffer:
            raise RoomException("Error generating SDP offer for publishing user " + name, Code.MEDIA_SDP_ERROR_CODE)

        room.newPublisher(participant)
        return sdpOffer

    def unpublishMedia(self, participantId):
        print("Request [UNPUBLISH_MEDIA] ({%d})" % participantId)

        participant = self.getParticipant(participantId)

        if not participant.isStreaming():
            raise RoomException("Participant '" + participant.getName() + "' is not streaming media",Code.USER_NOT_STREAMING_ERROR_CODE)

        room = participant.getRoom()
        participant.unpublishMedia()
        room.cancelPublisher(participant)

    def subscribe(self, remoteName, sdpOffer, participantId):
        print("Request [SUBSCRIBE] remoteParticipant={} sdpOffer={} ({})", remoteName, sdpOffer, participantId)

        participant = self.getParticipant(participantId)

        name = participant.getName()
        room = participant.getRoom()

        senderParticipant = room.getParticipantByName(remoteName)

        if not senderParticipant:
            print("PARTICIPANT {%s}: Requesting to recv media from user {%s} in room {%s} but user could not be found" % (name, remoteName, room.getName()))
            raise RoomException( "User '" + remoteName + " not found in room '" + room.getName() + "'", Code.USER_NOT_FOUND_ERROR_CODE)

        if not senderParticipant.isStreaming():
            print("PARTICIPANT {%s}: Requesting to recv media from user {%s} in room {%s} but user is not streaming media" % (name, remoteName, room.getName()))
            raise RoomException("User '" + remoteName + " not streaming media in room '" + room.getName() + "'", Code.USER_NOT_STREAMING_ERROR_CODE)

        sdpAnswer = participant.receiveMediaFrom(senderParticipant, sdpOffer)
        if not sdpAnswer:
            raise RoomException("Unable to generate SDP answer when subscribing '" + name + "' to '" + remoteName + "'", Code.MEDIA_SDP_ERROR_CODE)

        return sdpAnswer

    def unsubscribe(self, remoteName, participantId):

        print("Request [UNSUBSCRIBE] remoteParticipant={%s} ({%d})" % (remoteName, participantId))

        participant = self.getParticipant(participantId)
        name = participant.getName()
        room = participant.getRoom()
        senderParticipant = room.getParticipantByName(remoteName)

        if not senderParticipant:
            print("PARTICIPANT {%s}: Requesting to unsubscribe from user {%s} in room {%s} but user could not be found"
                  % (name, remoteName, room.getName()))
            raise RoomException("User " + remoteName + " not found in room " + room.getName(), Code.USER_NOT_FOUND_ERROR_CODE)

        participant.cancelReceivingMedia(remoteName)


    def onIceCandidate(self, endpointName, candidate, sdpMLineIndex, sdpMid, participantId):
        print("Request [ICE_CANDIDATE] endpoint={%s} candidate={%s} sdpMLineIdx={%s} sdpMid={%s} ({%s})" %
              (endpointName, candidate, sdpMLineIndex, sdpMid, participantId))
        participant = self.getParticipant(participantId)
        participant.addIceCandidate(endpointName, IceCandidate(candidate, sdpMid, sdpMLineIndex).serialize())
        # self.ice_candidates.append(dict(endpointName=endpointName, iceCandidate=IceCandidate(candidate, sdpMid, sdpMLineIndex).serialize()))


    def addMediaElement(self, participantId, element, media_type=None):
        print("Add media element {%s} (connection type: {%s}) to participant {%s}" % (element.getId(), media_type,
            participantId))

        participant = self.getParticipant(participantId)
        name = participant.getName()

        if participant.isClosed():
            raise RoomException( "Participant '" + name + "' has been closed", Code.USER_CLOSED_ERROR_CODE,)

        participant.shapePublisherMedia(element, type)

    def removeMediaElement(self, participantId, element):
        print("Remove media element {%s} from participant {%s}" % (element.getId(), participantId))

        participant = self.getParticipant(participantId)
        name = participant.getName()

        if participant.isClosed():
            raise RoomException("Participant '" + name + "' has been closed", Code.USER_CLOSED_ERROR_CODE)

        participant.getPublisher().revert(element)

    def mutePublishedMedia(self, muteType, participantId):
        print("Request [MUTE_PUBLISHED] muteType={%d} ({%d})" & muteType, participantId)
        participant = self.getParticipant(participantId)
        name = participant.getName()
        if participant.isClosed():
            print(Code.USER_CLOSED_ERROR_CODE, "Participant '" + name + "' has been closed")

        if not participant.isStreaming():
            raise RoomException("Participant '" + name + "' is not streaming media", Code.USER_NOT_STREAMING_ERROR_CODE)

        participant.mutePublishedMedia(muteType)

    def unmutePublishedMedia(self, participantId):
        print("Request [UNMUTE_PUBLISHED] ({%s})" % participantId)
        participant = self.getParticipant(participantId)
        name = participant.getName()

        if participant.isClosed():
            raise RoomException("Participant '" + name + "' has been closed", Code.USER_CLOSED_ERROR_CODE)

        if not participant.isStreaming():
            raise RoomException("Participant '" + name + "' is not streaming media", Code.USER_NOT_STREAMING_ERROR_CODE)

        participant.unmutePublishedMedia()

    def muteSubscribedMedia(self, remoteName, muteType, participantId):
        print("Request [MUTE_SUBSCRIBED] remoteParticipant={%d} muteType={%d} ({%d})" % (remoteName, muteType, participantId))

        participant = self.getParticipant(participantId)
        name = participant.getName()
        room = participant.getRoom()
        senderParticipant = room.getParticipantByName(remoteName)

        if not senderParticipant:
            print("PARTICIPANT {%s}: Requesting to mute streaming from {%s} in room {%s} but user could not be found"
                  % (name, remoteName, room.getName()))
            raise RoomException("User " + remoteName + " not found in room " + room.getName(), Code.USER_NOT_FOUND_ERROR_CODE,)

        if not senderParticipant.isStreaming():
            print("PARTICIPANT {%s}: Requesting to mute streaming from {%s} in room {%s} but user is not streaming media"
                  % (name, remoteName, room.getName()))

            raise RoomException("User '" + remoteName + " not streaming media in room '" + room.getName() + "'", Code.USER_NOT_STREAMING_ERROR_CODE)

        participant.muteSubscribedMedia(senderParticipant, muteType)

    def unmuteSubscribedMedia(self, remoteName, participantId):
        print("Request [UNMUTE_SUBSCRIBED] remoteParticipant={%s} ({%s})" % remoteName, participantId)
        participant = self.getParticipant(participantId)
        name = participant.getName()
        room = participant.getRoom()
        senderParticipant = room.getParticipantByName(remoteName)

        if not senderParticipant:
            print("PARTICIPANT {%s}: Requesting to unmute streaming from {%s} in room {%s} but user could not be found"
                  % (name, remoteName, room.getName()))
            raise RoomException("User " + remoteName + " not found in room " + room.getName(), Code.USER_NOT_FOUND_ERROR_CODE)

        if not senderParticipant.isStreaming():
            print("PARTICIPANT {%s}: Requesting to unmute streaming from {%s} in room {%s} but user is not streaming media"
                  % (name, remoteName, room.getName()))

            raise RoomException("User '" + remoteName + " not streaming media in room '" + room.getName() + "'", Code.USER_NOT_STREAMING_ERROR_CODE)
        participant.unmuteSubscribedMedia(senderParticipant)

    def saveCoordToFile(self, participantId, coordinates, windowSize, brushColor, brushSize, brushType):
        participant = self.getParticipant(participantId)

        if not participant:
            raise RoomException("No participant with id '" + participantId + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)

        filePath = participant.getRecorderedFileName()
        room = participant.getRoom()

        if not room:
            print("Room '{%s}' not found" % room)
            raise RoomException("Room '" + room.getName() + "' was not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        if room.isClosed():
            print("Room '{%s}' is closing" % room.getName())
            raise RoomException("Room " + room.getName() + "' but is closing", Code.ROOM_CLOSED_ERROR_CODE)

        existingParticipants = self.getParticipants(room.getName())
        room.saveCoord(filePath, coordinates, windowSize, brushColor, brushSize, brushType)
        return existingParticipants

    def recordSession(self, roomName, participantId):
        room = self.rooms.get(roomName)

        if not room:
            print("Room '{%s}' not found" % room)
            raise RoomException("Room '" + room.getName() + "' was not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        if room.isClosed():
            print("Room '{%s}' is closing" % room.getName())
            raise RoomException("Room " + room.getName() + "' but is closing", Code.ROOM_NOT_FOUND_ERROR_CODE)

        existingParticipants = self.getParticipants(roomName)
        room.recordSession(participantId)
        return existingParticipants

    def stopRecording(self, roomName, participantId):
        room = self.rooms.get(roomName)
        if not room:
            print("Room '{%s}' not found" % room)
            raise RoomException("Room '" + room.getName() + "' was not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        if room.isClosed():
            print("Room '{%s}' is closing" % room.getName())
            raise RoomException("Room " + room.getName() + "' but is closing", Code.ROOM_CLOSED_ERROR_CODE)

        existingParticipants = self.getParticipants(roomName)
        room.stopRecording(participantId)
        return existingParticipants


    def getherCandidates(self, participantId):

        print("Request [Get IceCandidate] ")
        participant = self.getParticipant(participantId)
        room = participant.getRoom()

        for candidate in self.kcProvider.getKurentoClient().get_ice_candidates():
            time.sleep(0.01)
            for key in room.participants:
                if room.participants[key].publisher.webEndpoint \
                        and room.participants[key].publisher.webEndpoint.id == candidate['source']:
                    participant.sendIceCandidate(participantId, room.participants[key].publisher.endpointName, candidate['candidate'])


    def call(self, senderName, toName, sdpOffer):
        print("Request [call] sender={%s} to={%s} sdpOffer={%s})", senderName, toName, sdpOffer)

        participant = self.getParticipantByName(toName)

        name = participant.getName()
        room = participant.getRoom()

        senderParticipant = room.getParticipantByName(senderName)

        if not senderParticipant:
            print("PARTICIPANT {%s}: Requesting to send media from user {%s} in room {%s} but user could not be found" % (
                senderName, name, room.getName()))
            raise RoomException("User '" + senderName + " not found in room '" + room.getName() + "'",
                                Code.USER_NOT_FOUND_ERROR_CODE)

        if not senderParticipant.isStreaming():
            print(
                "PARTICIPANT {%s}: Requesting to send media from user {%s} in room {%s} but user is not streaming media" % (
                    senderName, name, room.getName()))
            raise RoomException("User '" + senderName + " not streaming media in room '" + room.getName() + "'",
                                Code.USER_NOT_STREAMING_ERROR_CODE)

        sdpAnswer = participant.receiveMediaFrom(senderParticipant, sdpOffer)
        if not sdpAnswer:
            raise RoomException("Unable to generate SDP answer when call from '" + senderName + "' to '" + toName + "'",
                                Code.MEDIA_SDP_ERROR_CODE)

        return sdpAnswer


    # ----------------- ADMIN (DIRECT or SERVER-SIDE) REQUESTS ------------

    def close(self):
        self.closed = True
        print("Closing all rooms")

        for roomName in self.rooms.keys():
            try:
                self.closeRoom(roomName)
            except:
                print("Error closing room '{%s}'", roomName)

    def isClosed(self):
        return self.closed

    def getRooms(self):
        return list(self.rooms.keys())

    def getParticipants(self, roomName):

        room = self.rooms.get(roomName)
        if not room:
            raise RoomException("Room '" + roomName + "' not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        participants = room.getParticipants()
        userParts = []

        for p in participants:
            if not p.isClosed():
                userParts.append(UserParticipant(p.getId(), p.getName(), p.isStreaming()))

        return userParts

    def getPublishers(self, roomName):
        try:
            r = self.rooms.get(roomName)
        except:
            raise RoomException("Room '" + roomName + "' not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        participants = r.getParticipants()
        userParts = []

        for p in participants:
            if not p.isClosed() and p.isStreaming():
                userParts.append(UserParticipant(p.getId(), p.getName(), True))

        return userParts


    def getSubscribers(self, roomName):
        try:
            r = self.rooms.get(roomName)
        except:
            raise RoomException( "Room '" + roomName + "' not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        participants = r.getParticipants()
        userParts = []

        for p in participants:
            if not p.isClosed() and p.isSubscribed():
                userParts.append(UserParticipant(p.getId(), p.getName(), p.isStreaming()))

        return userParts

    def getPeerPublishers(self, participantId):

        participant = self.getParticipant(participantId)

        if not participant:
            raise RoomException("No participant with id '" + participantId + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)

        subscribedEndpoints = participant.getConnectedSubscribedEndpoints()
        room = participant.getRoom()
        userParts = []

        for epName in subscribedEndpoints:
            p = room.getParticipantByName(epName)
            userParts.append(UserParticipant(p.getId(), p.getName()))

        return userParts

    def getPeerSubscribers(self, participantId):
        participant = self.getParticipant(participantId)

        if not participant:
            raise RoomException("No participant with id '" + participantId + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)

        if not participant.isStreaming():
            raise RoomException("Participant with id '" + participantId + "' is not a publisher yet", Code.USER_NOT_STREAMING_ERROR_CODE)

        userParts = []
        room = participant.getRoom()
        endpointName = participant.getName()

        for p in room.getParticipants():
            if p==participant:
                continue
            subscribedEndpoints = p.getConnectedSubscribedEndpoints()
            if endpointName in subscribedEndpoints:
                userParts.append(UserParticipant(p.getId(), p.getName()))

        return userParts

    def isPublisherStreaming(self, participantId):
        participant = self.getParticipant(participantId)

        if not participant:
            raise RoomException("No participant with id '" + participantId + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)


        if participant.isClosed():
            raise RoomException("Participant '" + participant.getName() + "' has been closed", Code.USER_CLOSED_ERROR_CODE)

        return participant.isStreaming()

    def isPublisherRecording(self, participantId):
        participant = self.getParticipant(participantId)

        if not participant:
            raise RoomException("No participant with id '" + participantId + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)


        if participant.isClosed():
            raise RoomException("Participant '" + participant.getName() + "' has been closed", Code.USER_CLOSED_ERROR_CODE)

        return participant.isRecording()

    def createRoom(self, kcSessionInfo):
        roomName = kcSessionInfo.getRoomName()
        room = self.rooms.get(kcSessionInfo)

        if room:
            raise RoomException("Room '" + roomName + "' already exists", Code.ROOM_CANNOT_BE_CREATED_ERROR_CODE)

        kurentoClient = self.kcProvider.getKurentoClient(kcSessionInfo)

        room = Room(roomName, kurentoClient, self.roomHandler, self.kcProvider.destroyWhenUnused())
        if roomName in self.rooms.keys():
            print("Room '{}' has just been created by another thread" % roomName)
            return
        self.rooms[roomName] = room

        # kcName = "[NAME NOT AVAILABLE]"
        # if kurentoClient.getServerManager():
        #     kcName = kurentoClient.getServerManager().getName()

        print("No room '{%s}' exists yet. Created one using KurentoClient ''." % (roomName))

    def closeRoom(self,roomName):
        room = self.rooms.get(roomName)
        if not room:
            raise RoomException("Room '" + roomName + "' not found", Code.ROOM_NOT_FOUND_ERROR_CODE)

        if room.isClosed():
            raise RoomException("Room '" + roomName + "' already closed", Code.ROOM_CLOSED_ERROR_CODE,)

        participants = self.getParticipants(roomName)
        pids = room.getParticipantIds()

        for pid in pids:
            try:
                room.leave(pid)
            except Exception as e:
                print("Error evicting participant with id '{%s}' from room '{%s}'" % (pid, roomName))

        room.close()
        self.rooms.pop(roomName)
        print("Room '{%s}' removed and closed", roomName)
        return participants

    def getPipeline(self, participantId):
        participant = self.getParticipant(participantId)
        if not participant:
            raise RoomException("No participant with id '" + participantId + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)
        return participant.getPipeline()

    def getRoomName(self, participantId):
        participant = self.getParticipant(participantId)
        return participant.getRoom().getName()

    def getParticipantName(self, participantId):
        participant = self.getParticipant(participantId)
        return participant.getName()

    def getParticipantInfo(self, participantId):
        participant = self.getParticipant(participantId)
        return UserParticipant(participantId, participant.getName())

    #------------------ HELPERS ------------------------------------------

    def getParticipant(self, pid):
        for r in self.rooms.values():
            if not r.isClosed():
                if pid in r.getParticipantIds() and r.getParticipant(pid):
                    return r.getParticipant(pid)
        if self.rooms:
            raise RoomException("No participant with id '" + str(pid) + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)

    def updateFilter(self, roomId, filterId):
        room = self.rooms.get(roomId)
        room.updateFilter(filterId)


    def getParticipantByName(self, userName):
        for r in self.rooms.values():
            if not r.isClosed():
                for p in r.participants.values():
                    if p.getName() == userName:
                        return p


        raise RoomException("No participant with Name '" + userName + "' was found", Code.USER_NOT_FOUND_ERROR_CODE)

